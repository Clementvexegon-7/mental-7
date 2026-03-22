# ================================================================
#  mentalapp/forms.py
# ================================================================

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Mood, JournalEntry, Checklist, SavedResource, UserProfile, ContactMessage, Appointment


# ── AUTHENTICATION ─────────────────────────────────────────────
class UserRegisterForm(UserCreationForm):
    email      = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name  = forms.CharField(max_length=30, required=False)

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email      = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
            UserProfile.objects.get_or_create(user=user)
        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


# ── PROFILE ────────────────────────────────────────────────────
class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name  = forms.CharField(max_length=30, required=False)
    email      = forms.EmailField(required=False)

    class Meta:
        model   = UserProfile
        fields  = ['bio', 'avatar', 'date_of_birth', 'location']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'bio':           forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial  = user.last_name
            self.fields['email'].initial      = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name', '')
        user.email      = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            profile.save()
        return profile


# ── MOOD ───────────────────────────────────────────────────────
class MoodForm(forms.ModelForm):
    class Meta:
        model   = Mood
        fields  = ['mood_score', 'notes', 'date']
        widgets = {
            'date':  forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'How are you feeling? What happened today?'}),
        }
        labels = {
            'mood_score': 'How are you feeling today?',
            'notes':      'Notes (optional)',
        }


# ── JOURNAL ────────────────────────────────────────────────────
class JournalForm(forms.ModelForm):
    class Meta:
        model   = JournalEntry
        fields  = ['title', 'content', 'is_private']
        widgets = {
            'title':   forms.TextInput(attrs={'placeholder': 'Entry title…'}),
            'content': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Write your thoughts freely…'}),
        }
        labels = {
            'is_private': 'Keep this entry private',
        }


# ── CHECKLIST ──────────────────────────────────────────────────
class ChecklistForm(forms.ModelForm):
    class Meta:
        model  = Checklist
        fields = [
            'slept_well', 'exercised', 'ate_well', 'stayed_hydrated',
            'meditated', 'journaled', 'limited_screens',
            'connected_others', 'set_boundaries',
            'spent_time_outside', 'expressed_gratitude',
        ]
        labels = {
            'slept_well':          'Slept at least 7 hours',
            'exercised':           'Exercised / moved my body',
            'ate_well':            'Ate balanced meals',
            'stayed_hydrated':     'Stayed hydrated',
            'meditated':           'Meditated / practised mindfulness',
            'journaled':           'Journaled or reflected',
            'limited_screens':     'Limited screen time',
            'connected_others':    'Connected with someone I care about',
            'set_boundaries':      'Set healthy boundaries',
            'spent_time_outside':  'Spent time outdoors',
            'expressed_gratitude': 'Expressed gratitude',
        }


# ── SAVED RESOURCE ─────────────────────────────────────────────
class SavedResourceForm(forms.ModelForm):
    class Meta:
        model   = SavedResource
        fields  = ['resource_type', 'title', 'description', 'url', 'phone_number', 'notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief description…'}),
            'notes':       forms.Textarea(attrs={'rows': 3, 'placeholder': 'Personal notes…'}),
            'url':         forms.URLInput(attrs={'placeholder': 'https://…'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'e.g. 0722 178 177'}),
        }
        labels = {
            'resource_type': 'Type of Resource',
            'phone_number':  'Phone Number (if hotline)',
        }


# ── CONTACT MESSAGE ────────────────────────────────────────────
class ContactMessageForm(forms.ModelForm):
    class Meta:
        model   = ContactMessage
        fields  = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Your message…'}),
            'subject': forms.TextInput(attrs={'placeholder': 'What is this about?'}),
            'name':    forms.TextInput(attrs={'placeholder': 'Your name'}),
            'email':   forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
        }


# ── APPOINTMENT ────────────────────────────────────────────────
class AppointmentForm(forms.ModelForm):
    class Meta:
        model  = Appointment
        fields = ['appointment_type', 'preferred_date', 'preferred_time', 'therapist_name', 'location', 'notes']
        widgets = {
            'appointment_type': forms.Select(attrs={'class': 'form-select appt-input'}),
            'preferred_date':   forms.DateInput(attrs={'class': 'form-control appt-input', 'type': 'date'}),
            'preferred_time':   forms.TimeInput(attrs={'class': 'form-control appt-input', 'type': 'time'}),
            'therapist_name':   forms.TextInput(attrs={'class': 'form-control appt-input', 'placeholder': 'e.g. Dr. Amara Osei (optional)'}),
            'location':         forms.TextInput(attrs={'class': 'form-control appt-input', 'placeholder': 'Clinic address or "Online"'}),
            'notes':            forms.Textarea(attrs={'class': 'form-control appt-input', 'rows': 4, 'placeholder': "Anything your therapist should know beforehand…"}),
        }
        labels = {
            'appointment_type': 'Type of Session',
            'preferred_date':   'Preferred Date',
            'preferred_time':   'Preferred Time',
            'therapist_name':   'Therapist / Counsellor (optional)',
            'location':         'Location',
            'notes':            'Additional Notes',
        }

    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        if date and date < timezone.localdate():
            raise forms.ValidationError("Please choose a future date.")
        return date