# ================================================================
#  mentalapp/admin.py
# ================================================================

from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, Mood, JournalEntry, Checklist, SavedResource, ContactMessage, Appointment


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display    = ('user', 'location', 'created_at')
    search_fields   = ('user__username', 'user__email', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display   = ('user', 'mood_score_display', 'date', 'created_at')
    list_filter    = ('mood_score', 'date')
    search_fields  = ('user__username',)
    date_hierarchy = 'date'

    def mood_score_display(self, obj):
        return f"{obj.mood_emoji} {obj.get_mood_score_display()} ({obj.mood_score}/10)"
    mood_score_display.short_description = 'Mood'


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display    = ('user', 'title', 'is_private', 'created_at')
    list_filter     = ('is_private',)
    search_fields   = ('user__username', 'title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display   = ('user', 'date', 'score_display', 'percent_display', 'emotional_label')
    search_fields  = ('user__username',)
    date_hierarchy = 'date'
    list_filter    = ('date',)

    def score_display(self, obj):
        return f"{obj.completion_score}/11"
    score_display.short_description = 'Score'

    def percent_display(self, obj):
        pct = obj.completion_percent
        colour = '#2e7d32' if pct >= 70 else '#f57f17' if pct >= 40 else '#c62828'
        return format_html('<span style="color:{};font-weight:700">{}%</span>', colour, pct)
    percent_display.short_description = 'Completion'

    def emotional_label(self, obj):
        return obj.emotional_label
    emotional_label.short_description = 'Feedback'


@admin.register(SavedResource)
class SavedResourceAdmin(admin.ModelAdmin):
    list_display  = ('user', 'title', 'resource_type', 'saved_at')
    list_filter   = ('resource_type',)
    search_fields = ('user__username', 'title')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display    = ('name', 'email', 'subject', 'status_badge', 'created_at')
    list_filter     = ('status',)
    search_fields   = ('name', 'email', 'subject')
    readonly_fields = ('created_at',)
    actions         = ['mark_as_read', 'mark_as_replied']

    def status_badge(self, obj):
        colours = {'new': '#c62828', 'read': '#f57f17', 'replied': '#2e7d32', 'archived': '#9e9e9e'}
        colour  = colours.get(obj.status, '#9e9e9e')
        return format_html('<span style="background:{};color:#fff;padding:2px 8px;border-radius:20px;font-size:.8rem">{}</span>', colour, obj.get_status_display())
    status_badge.short_description = 'Status'

    def mark_as_read(self, request, queryset):
        queryset.update(status='read')
    mark_as_read.short_description = 'Mark selected as Read'

    def mark_as_replied(self, request, queryset):
        queryset.update(status='replied')
    mark_as_replied.short_description = 'Mark selected as Replied'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display   = ('user', 'appointment_type', 'preferred_date', 'preferred_time', 'status_badge', 'created_at')
    list_filter    = ('status', 'appointment_type', 'preferred_date')
    search_fields  = ('user__username', 'therapist_name')
    date_hierarchy = 'preferred_date'
    actions        = ['confirm_appointments']

    def status_badge(self, obj):
        colours = {'pending': '#f57f17', 'confirmed': '#2e7d32', 'cancelled': '#c62828', 'completed': '#1565c0'}
        colour  = colours.get(obj.status, '#9e9e9e')
        return format_html('<span style="background:{};color:#fff;padding:2px 8px;border-radius:20px;font-size:.8rem">{}</span>', colour, obj.get_status_display())
    status_badge.short_description = 'Status'

    def confirm_appointments(self, request, queryset):
        queryset.filter(status='pending').update(status='confirmed')
    confirm_appointments.short_description = 'Confirm selected appointments'