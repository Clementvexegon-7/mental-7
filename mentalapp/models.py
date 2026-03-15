# ================================================================
#  mentalapp/models.py
# ================================================================

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# ─────────────────────────────────────────────
#  USER PROFILE
# ─────────────────────────────────────────────
class UserProfile(models.Model):
    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio           = models.TextField(blank=True, null=True)
    avatar        = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    location      = models.CharField(max_length=120, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Auto-create profile when a new User is created via signal
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


# ─────────────────────────────────────────────
#  MOOD TRACKER
# ─────────────────────────────────────────────
class Mood(models.Model):
    MOOD_CHOICES = [
        (1,  'Very Low'),       (2,  'Low'),           (3,  'Below Average'),
        (4,  'Slightly Low'),   (5,  'Neutral'),        (6,  'Slightly Good'),
        (7,  'Good'),           (8,  'Very Good'),      (9,  'Excellent'),
        (10, 'Outstanding'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_entries')
    mood_score = models.IntegerField(choices=MOOD_CHOICES)
    notes      = models.TextField(blank=True, null=True)
    date       = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Mood Entry'
        verbose_name_plural = 'Mood Entries'
        ordering            = ['-date', '-created_at']
        unique_together     = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} — {self.get_mood_score_display()} on {self.date}"

    @property
    def mood_emoji(self):
        emojis = {
            1: '😞', 2: '😟', 3: '😕', 4: '😐', 5: '😶',
            6: '🙂', 7: '😊', 8: '😁', 9: '😄', 10: '🤩',
        }
        return emojis.get(self.mood_score, '❓')


# ─────────────────────────────────────────────
#  JOURNAL ENTRY
# ─────────────────────────────────────────────
class JournalEntry(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    title      = models.CharField(max_length=200)
    content    = models.TextField()
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.title[:50]}"

    def short_content(self):
        return self.content[:150] + ('…' if len(self.content) > 150 else '')


# ─────────────────────────────────────────────
#  SELF-CARE CHECKLIST
# ─────────────────────────────────────────────
class Checklist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='selfcare_logs')
    date = models.DateField(default=timezone.now)

    # Body
    slept_well      = models.BooleanField(default=False)
    exercised       = models.BooleanField(default=False)
    ate_well        = models.BooleanField(default=False)
    stayed_hydrated = models.BooleanField(default=False)

    # Mind
    meditated       = models.BooleanField(default=False)
    journaled       = models.BooleanField(default=False)
    limited_screens = models.BooleanField(default=False)

    # Social
    connected_others = models.BooleanField(default=False)
    set_boundaries   = models.BooleanField(default=False)

    # Spirit
    spent_time_outside  = models.BooleanField(default=False)
    expressed_gratitude = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Self-Care Checklist'
        verbose_name_plural = 'Self-Care Checklists'
        ordering            = ['-date']
        unique_together     = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} — Self-Care on {self.date}"

    @property
    def completion_score(self):
        fields = [
            self.slept_well, self.exercised, self.ate_well, self.stayed_hydrated,
            self.meditated, self.journaled, self.limited_screens,
            self.connected_others, self.set_boundaries,
            self.spent_time_outside, self.expressed_gratitude,
        ]
        return sum(fields)

    @property
    def completion_percent(self):
        return round((self.completion_score / 11) * 100)


# ─────────────────────────────────────────────
#  SAVED RESOURCE
# ─────────────────────────────────────────────
class SavedResource(models.Model):
    RESOURCE_TYPES = [
        ('hotline',   'Crisis Hotline'),
        ('therapy',   'Therapy / Counseling'),
        ('app',       'Mental Health App'),
        ('article',   'Article / Guide'),
        ('community', 'Community / Support Group'),
        ('other',     'Other'),
    ]

    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_resources')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='other')
    title         = models.CharField(max_length=200)
    description   = models.TextField(blank=True)
    url           = models.URLField(blank=True, null=True)
    phone_number  = models.CharField(max_length=30, blank=True)
    notes         = models.TextField(blank=True)
    saved_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Saved Resource'
        verbose_name_plural = 'Saved Resources'
        ordering            = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} saved: {self.title}"


# ─────────────────────────────────────────────
#  CONTACT MESSAGE
# ─────────────────────────────────────────────
class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new',      'New'),
        ('read',     'Read'),
        ('replied',  'Replied'),
        ('archived', 'Archived'),
    ]

    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_messages')
    name       = models.CharField(max_length=120)
    email      = models.EmailField()
    subject    = models.CharField(max_length=250)
    message    = models.TextField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering            = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.subject} from {self.name}"


# ─────────────────────────────────────────────
#  APPOINTMENT
# ─────────────────────────────────────────────
class Appointment(models.Model):

    APPOINTMENT_TYPE_CHOICES = [
        ('individual', 'Individual Therapy'),
        ('group',      'Group Session'),
        ('assessment', 'Mental Health Assessment'),
        ('follow_up',  'Follow-Up Consultation'),
        ('crisis',     'Crisis Support'),
    ]

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    user             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.CharField(max_length=50, choices=APPOINTMENT_TYPE_CHOICES, default='individual')
    preferred_date   = models.DateField()
    preferred_time   = models.TimeField()
    therapist_name   = models.CharField(max_length=120, blank=True)
    location         = models.CharField(
        max_length=200, blank=True,
        help_text="Clinic address or 'Online' for virtual sessions"
    )
    notes      = models.TextField(
        blank=True,
        help_text="Any additional information or concerns you'd like to share"
    )
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['preferred_date', 'preferred_time']
        verbose_name        = 'Appointment'
        verbose_name_plural = 'Appointments'

    def __str__(self):
        return (
            f"{self.user.username} — "
            f"{self.get_appointment_type_display()} on "
            f"{self.preferred_date} at {self.preferred_time}"
        )

    def is_upcoming(self):
        return self.preferred_date >= timezone.localdate()