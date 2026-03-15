# ================================================================
#  mentalapp/urls.py
# ================================================================

from django.urls import path
from . import views

app_name = 'mentalapp'

urlpatterns = [

    # ── HOME & INFO PAGES ──────────────────────────────────────
    path('',                        views.home_view,      name='home'),
    path('about/',                  views.about,          name='about'),
    path('conditions/',             views.conditions,     name='conditions'),
    path('signs/',                  views.signs,          name='signs'),
    path('prevention/',             views.prevention,     name='prevention'),
    path('selfcare/',               views.selfcare_info,  name='selfcare'),
    path('resources/',              views.resources_info, name='resources'),
    path('contact/',                views.contact,        name='contact'),

    # ── AUTHENTICATION ─────────────────────────────────────────
    path('register/',               views.register_view,  name='register'),
    path('login/',                  views.login_view,     name='login'),
    path('logout/',                 views.logout_view,    name='logout'),

    # ── DASHBOARD ──────────────────────────────────────────────
    path('dashboard/',              views.dashboard,      name='dashboard'),

    # ── MOOD TRACKER ───────────────────────────────────────────
    path('mood/',                   views.mood_list,      name='mood_list'),
    path('mood/new/',               views.mood_create,    name='mood_create'),
    path('mood/<int:pk>/edit/',     views.mood_edit,      name='mood_edit'),
    path('mood/<int:pk>/delete/',   views.mood_delete,    name='mood_delete'),

    # ── JOURNAL ────────────────────────────────────────────────
    path('journal/',                views.journal_list,   name='journal_list'),
    path('journal/new/',            views.journal_create, name='journal_create'),
    path('journal/<int:pk>/',       views.journal_detail, name='journal_detail'),
    path('journal/<int:pk>/edit/',  views.journal_edit,   name='journal_edit'),
    path('journal/<int:pk>/delete/', views.journal_delete, name='journal_delete'),

    # ── SELF-CARE CHECKLIST ────────────────────────────────────
    path('checklist/',              views.checklist_today,   name='checklist_today'),
    path('checklist/history/',      views.checklist_history, name='checklist_history'),

    # ── SAVED RESOURCES ────────────────────────────────────────
    path('saved/',                  views.saved_resources,        name='saved_resources'),
    path('saved/add/',              views.save_resource,          name='save_resource'),
    path('saved/<int:pk>/delete/',  views.delete_saved_resource,  name='delete_saved_resource'),

    # ── PROFILE ────────────────────────────────────────────────
    path('profile/',                views.profile,      name='profile'),
    path('profile/edit/',           views.profile_edit, name='profile_edit'),

    # ── APPOINTMENTS ───────────────────────────────────────────
    path('appointments/',                       views.appointment_list,   name='appointment_list'),
    path('appointments/book/',                  views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/edit/',         views.appointment_edit,   name='appointment_edit'),
    path('appointments/<int:pk>/cancel/',       views.appointment_cancel, name='appointment_cancel'),
]