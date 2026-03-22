# ================================================================
#  mental/urls.py  — Project-level URL configuration
# ================================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

# ── Customise admin header ────────────────────────────────────
admin.site.site_header  = 'MindWell Admin'
admin.site.site_title   = 'MindWell Admin Portal'
admin.site.index_title  = 'mentalhealthcare_ke Dashboard'

urlpatterns = [

    # ── DJANGO ADMIN ─────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── MAIN APP ──────────────────────────────────────────────
    path('', include('mentalapp.urls', namespace='mentalapp')),

    # ── PASSWORD RESET FLOW ───────────────────────────────────
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='mentalapp/password_reset.html',
            email_template_name='mentalapp/password_reset_email.html',
            subject_template_name='mentalapp/password_reset_subject.txt',
            extra_context={'site_name': 'MindWell'},
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='mentalapp/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='mentalapp/password_reset_confirm.html'
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='mentalapp/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),
]

# ── MEDIA FILES (dev only) ────────────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)