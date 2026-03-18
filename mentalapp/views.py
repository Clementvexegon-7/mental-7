# ================================================================
#  mentalapp/views.py
# ================================================================

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# ── MODELS ─────────────────────────────────────────────────────
from .models import (
    Mood, JournalEntry, SavedResource, Checklist,
    UserProfile, ContactMessage, Appointment,
)

# ── FORMS ──────────────────────────────────────────────────────
from .forms import (
    UserRegisterForm,
    UserProfileForm,
    LoginForm,
    MoodForm,
    JournalForm,
    ChecklistForm,
    SavedResourceForm,
    ContactMessageForm,
    AppointmentForm,
)


# ── HOME & INFO PAGES ──────────────────────────────────────────
def home_view(request):
    return render(request, 'mentalapp/index.html')

def about(request):
    return render(request, 'mentalapp/about.html')

def conditions(request):
    return render(request, 'mentalapp/conditions.html')

def signs(request):
    return render(request, 'mentalapp/signs.html')

def prevention(request):
    return render(request, 'mentalapp/prevention.html')

def selfcare_info(request):
    return render(request, 'mentalapp/selfcare.html')

def resources_info(request):
    return render(request, 'mentalapp/resources.html')


def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            if request.user.is_authenticated:
                msg.user = request.user
            msg.save()
            messages.success(request, "Your message has been sent!")
            return redirect('mentalapp:home')
    else:
        form = ContactMessageForm()
    return render(request, 'mentalapp/contact.html', {'form': form})


# ── AUTHENTICATION ─────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in!")
        return redirect('mentalapp:home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome 🎉")
            return redirect('mentalapp:home')
    else:
        form = UserRegisterForm()

    return render(request, 'mentalapp/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in!")
        return redirect('mentalapp:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('mentalapp:home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'mentalapp/login.html', {'next': request.GET.get('next', '')})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('mentalapp:home')


# ── DASHBOARD ──────────────────────────────────────────────────
@login_required
def dashboard(request):
    today           = timezone.now().date()
    recent_moods    = Mood.objects.filter(user=request.user).order_by('-date')[:5]
    recent_journals = JournalEntry.objects.filter(user=request.user).order_by('-created_at')[:3]
    today_checklist = Checklist.objects.filter(user=request.user, date=today).first()
    upcoming_appointments = Appointment.objects.filter(
        user=request.user,
        preferred_date__gte=today,
        status__in=('pending', 'confirmed'),
    ).order_by('preferred_date', 'preferred_time')[:3]

    context = {
        'recent_moods':           recent_moods,
        'recent_journals':        recent_journals,
        'today_checklist':        today_checklist,
        'today':                  today,
        'upcoming_appointments':  upcoming_appointments,
    }
    return render(request, 'mentalapp/dashboard.html', context)


# ══════════════════════════════════════════════════════════════
#  MWENDO AI CHAT ENDPOINT
#  POST /mwendo-chat/   { "message": "...", "history": [...] }
#  Returns { "reply": "...", "quick": [...], "action": null }
#
#  NOTE: Add this URL to urls.py:
#     path('mwendo-chat/', views.mwendo_chat, name='mwendo_chat'),
# ══════════════════════════════════════════════════════════════
@require_POST
def mwendo_chat(request):
    """
    Context-aware Mwendo AI endpoint.

    Reads the user's recent moods & journal entries (if authenticated)
    and generates a personalised, compassionate reply.

    Request body (JSON):
        message  – user's raw text input
        history  – list of {"role":"user"|"bot", "text":"..."} (last 6)

    Response (JSON):
        reply    – Mwendo's response text (supports **bold** markdown)
        quick    – list of quick-reply button labels
        action   – "breathe" | "open_chat" | null
        redirect – MW_URLS key to redirect to, or null
    """
    try:
        body    = json.loads(request.body)
        message = body.get('message', '').strip()[:500]
        history = body.get('history', [])[-6:]          # last 6 turns only
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    low = message.lower()

    # ── Gather user context if authenticated ──────────────────
    user_context = {}
    if request.user.is_authenticated:
        recent_moods = list(
            Mood.objects.filter(user=request.user)
            .order_by('-date')[:5]
            .values('score', 'label', 'date')
        )
        recent_journals = list(
            JournalEntry.objects.filter(user=request.user)
            .order_by('-created_at')[:3]
            .values('title', 'created_at')
        )
        user_context = {
            'name':    request.user.get_short_name() or request.user.username,
            'moods':   recent_moods,
            'journals': recent_journals,
        }

    name_prefix = f"{user_context.get('name', '')}, " if user_context.get('name') else ""

    # ── Mood-aware personalisation ────────────────────────────
    mood_note = ""
    if user_context.get('moods'):
        scores  = [m['score'] for m in user_context['moods'] if m.get('score')]
        if scores:
            avg = sum(scores) / len(scores)
            if avg <= 3:
                mood_note = "I can see from your recent check-ins that things have been heavy lately. "
            elif avg >= 7:
                mood_note = "Your recent mood logs show you've been doing better — that matters. "

    # ── Crisis detection (highest priority) ──────────────────
    if any(kw in low for kw in ['crisis','suicid','kill','harm','hurt myself','end it','die','want to die']):
        return JsonResponse({
            'reply': f"{name_prefix}You matter deeply. Please reach out right now — a real person is ready to listen:\n\n🆘 **Befrienders Kenya: 0722 178 177** (24/7 · Free)\n📍 Mathari Hospital: **+254 20 2724069**\n🚑 Emergency: **999 / 112**\n\nI'm staying right here with you. You are not alone.",
            'quick': ['Call 0722 178 177', "I'm scared but okay", 'Stay with me', '🧘 Help me breathe'],
            'action': None,
            'redirect': None,
            'crisis': True,
        })

    # ── Anxiety ───────────────────────────────────────────────
    if any(kw in low for kw in ['anxi','panic','worry','stressed','overwhelm','scared','fear']):
        return JsonResponse({
            'reply': f"{mood_note}Anxiety is real, and it can feel relentless. 💙 Your nervous system is trying to protect you — it's just being a little too enthusiastic right now.\n\nLet's slow things down together. Would a 4-minute breathing exercise help?",
            'quick': ['🧘 Yes, let\'s breathe', 'Learn about anxiety', 'Tell me more', '🆘 I need crisis support'],
            'action': None,
            'redirect': None,
        })

    # ── Sadness / Depression ──────────────────────────────────
    if any(kw in low for kw in ['sad','depress','cry','hopeless','empty','alone','lonely','worthless','numb']):
        return JsonResponse({
            'reply': f"{mood_note}Thank you for trusting me with this. 💚 {name_prefix}Sadness doesn't mean weakness — it means something hurts, and that hurt deserves care.\n\nYou reached out today. That's not nothing — that's everything. Can I ask — are you safe right now?",
            'quick': ["Yes, I'm safe", 'I need crisis support', 'Find support near me', '🧘 Help me breathe'],
            'action': None,
            'redirect': None,
        })

    # ── Exhaustion / Burnout ──────────────────────────────────
    if any(kw in low for kw in ['tired','exhaust','burnout','no energy','drain','sleep','worn out']):
        return JsonResponse({
            'reply': f"Your body and mind are sending you a signal. 🌙 {mood_note}Rest is not giving up — it's maintenance for the most important thing you own: yourself.\n\nLet's find something that helps you recover.",
            'quick': ['Self-care guide', '🧘 Try breathing', 'Tell me more', 'Find resources'],
            'action': None,
            'redirect': None,
        })

    # ── Anger / Frustration ───────────────────────────────────
    if any(kw in low for kw in ['angry','mad','frustrated','rage','annoyed','furious']):
        return JsonResponse({
            'reply': f"Frustration usually means something genuinely matters to you. 🔥 That's not a character flaw — it's information.\n\nWhat's been weighing on you most?",
            'quick': ['Work / school pressure', 'Relationships', 'Feeling unheard', 'Everything at once'],
            'action': None,
            'redirect': None,
        })

    # ── Breathing request ─────────────────────────────────────
    if any(kw in low for kw in ['breath','breathe','breathing','calm down','relax']):
        return JsonResponse({
            'reply': "Let's breathe together. 🌿 Box breathing — inhale 4, hold 4, exhale 6, hold 4. Starting now.",
            'quick': [],
            'action': 'breathe',
            'redirect': None,
        })

    # ── Resource requests ─────────────────────────────────────
    if any(kw in low for kw in ['therapist','counsellor','help','support','resource','find','doctor','hospital']):
        return JsonResponse({
            'reply': f"There are people ready to support you. 💚 Our resources page has therapists, crisis lines, support groups, and apps — all vetted and free to browse.",
            'quick': ['Open resources page', 'Crisis lines only', 'Talk more first'],
            'action': None,
            'redirect': 'resources',
        })

    # ── Positive / Doing well ─────────────────────────────────
    if any(kw in low for kw in ['good','great','happy','fine','okay','well','better','grateful','thankful']):
        mood_celebration = ""
        if user_context.get('moods'):
            mood_celebration = " Your recent check-ins reflect that too — keep going."
        return JsonResponse({
            'reply': f"That genuinely makes me happy to hear. 🌟{mood_celebration}\n\nWould you like to explore something today, or just check in?",
            'quick': ['Self-care guide', 'Explore the site', 'Prevention strategies', 'Just saying hi 😊'],
            'action': None,
            'redirect': None,
        })

    # ── Journal / Writing ─────────────────────────────────────
    if any(kw in low for kw in ['journal','write','diary','record','track']):
        journal_note = ""
        if user_context.get('journals'):
            journal_note = f" I can see you've been journaling — that's one of the most powerful tools for mental clarity."
        return JsonResponse({
            'reply': f"Journaling is one of the most underrated forms of self-care.{journal_note} 📖 Writing your thoughts gives them a place to live outside your head.",
            'quick': ['Open my journal', 'Why journaling helps', 'Tell me more'],
            'action': None,
            'redirect': 'journal_list' if request.user.is_authenticated else None,
        })

    # ── Appointment / Therapy ─────────────────────────────────
    if any(kw in low for kw in ['appointment','book','session','therapy','therapist','schedule']):
        return JsonResponse({
            'reply': "Booking a session is a powerful act of self-care. 📅 Our appointment system lets you choose the type, mode, and time that works for you.",
            'quick': ['Book an appointment', 'What session types exist?', 'I\'m not sure yet'],
            'action': None,
            'redirect': 'appointment_list',
        })

    # ── Default / Unknown ────────────────────────────────────
    # Build a context-aware default using mood history
    default_opener = f"{mood_note}I hear you. 💚" if mood_note else "I hear you. 💚"
    return JsonResponse({
        'reply': f"{default_opener} Whatever you're carrying right now — it's real, it matters, and you deserve care.\n\nWhat would feel most helpful right now?",
        'quick': ['Find resources', 'Self-care guide', '🧘 Try breathing', 'Just talk'],
        'action': None,
        'redirect': None,
    })


# ── MOOD TRACKER ───────────────────────────────────────────────
@login_required
def mood_list(request):
    moods = Mood.objects.filter(user=request.user).order_by('-date')
    return render(request, 'mentalapp/mood_list.html', {'moods': moods})


@login_required
def mood_create(request):
    if request.method == 'POST':
        form = MoodForm(request.POST)
        if form.is_valid():
            mood = form.save(commit=False)
            mood.user = request.user
            mood.save()
            messages.success(request, "Mood logged!")
            return redirect('mentalapp:mood_list')
    else:
        form = MoodForm(initial={'date': timezone.now().date()})
    return render(request, 'mentalapp/mood_form.html', {'form': form, 'action': 'Log'})


@login_required
def mood_edit(request, pk):
    mood = get_object_or_404(Mood, pk=pk, user=request.user)
    if request.method == 'POST':
        form = MoodForm(request.POST, instance=mood)
        if form.is_valid():
            form.save()
            messages.success(request, "Mood updated!")
            return redirect('mentalapp:mood_list')
    else:
        form = MoodForm(instance=mood)
    return render(request, 'mentalapp/mood_form.html', {'form': form, 'action': 'Edit'})


@login_required
def mood_delete(request, pk):
    mood = get_object_or_404(Mood, pk=pk, user=request.user)
    if request.method == 'POST':
        mood.delete()
        messages.success(request, "Mood entry deleted.")
        return redirect('mentalapp:mood_list')
    return render(request, 'mentalapp/mood_confirm_delete.html', {'mood': mood})


# ── JOURNAL ────────────────────────────────────────────────────
@login_required
def journal_list(request):
    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'mentalapp/journal_list.html', {'entries': entries})


@login_required
def journal_create(request):
    if request.method == 'POST':
        form = JournalForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            messages.success(request, "Journal entry saved!")
            return redirect('mentalapp:journal_list')
    else:
        form = JournalForm()
    return render(request, 'mentalapp/journal_form.html', {'form': form, 'action': 'New'})


@login_required
def journal_detail(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    return render(request, 'mentalapp/journal_detail.html', {'entry': entry})


@login_required
def journal_edit(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        form = JournalForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Journal entry updated!")
            return redirect('mentalapp:journal_list')
    else:
        form = JournalForm(instance=entry)
    return render(request, 'mentalapp/journal_form.html', {'form': form, 'action': 'Edit'})


@login_required
def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, "Journal entry deleted.")
        return redirect('mentalapp:journal_list')
    return render(request, 'mentalapp/journal_confirm_delete.html', {'entry': entry})


# ── SELF-CARE CHECKLIST ────────────────────────────────────────
@login_required
def checklist_today(request):
    today = timezone.now().date()
    checklist, created = Checklist.objects.get_or_create(user=request.user, date=today)

    if request.method == 'POST':
        form = ChecklistForm(request.POST, instance=checklist)
        if form.is_valid():
            form.save()
            messages.success(request, "Checklist updated!")
            return redirect('mentalapp:checklist_today')
    else:
        form = ChecklistForm(instance=checklist)

    return render(request, 'mentalapp/checklist_today.html', {
        'form':      form,
        'checklist': checklist,
        'today':     today,
        'created':   created,
    })


@login_required
def checklist_history(request):
    items = Checklist.objects.filter(user=request.user).order_by('-date')
    return render(request, 'mentalapp/checklist_history.html', {'items': items})


# ── SAVED RESOURCES ────────────────────────────────────────────
@login_required
def saved_resources(request):
    resources = SavedResource.objects.filter(user=request.user)
    return render(request, 'mentalapp/saved_resources.html', {'resources': resources})


@login_required
def save_resource(request):
    if request.method == 'POST':
        form = SavedResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.user = request.user
            resource.save()
            messages.success(request, "Resource saved!")
            return redirect('mentalapp:saved_resources')
    else:
        form = SavedResourceForm()
    return render(request, 'mentalapp/save_resource_form.html', {'form': form})


@login_required
def delete_saved_resource(request, pk):
    resource = get_object_or_404(SavedResource, pk=pk, user=request.user)
    if request.method == 'POST':
        resource.delete()
        messages.success(request, "Resource removed.")
        return redirect('mentalapp:saved_resources')
    return render(request, 'mentalapp/saved_resource_confirm_delete.html', {'resource': resource})


# ── PROFILE ────────────────────────────────────────────────────
@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'mentalapp/profile.html', {'profile': profile_obj})


@login_required
def profile_edit(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('mentalapp:profile')
    else:
        form = UserProfileForm(instance=profile_obj)
    return render(request, 'mentalapp/profile_edit.html', {'form': form})


# ── APPOINTMENTS ───────────────────────────────────────────────
@login_required
def appointment_list(request):
    appointments = Appointment.objects.filter(user=request.user)
    return render(request, 'mentalapp/appointment_list.html', {'appointments': appointments})


@login_required
def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.user = request.user
            appt.save()
            messages.success(request, "Your appointment has been booked! We'll confirm it shortly.")
            return redirect('mentalapp:appointment_list')
    else:
        form = AppointmentForm()
    return render(request, 'mentalapp/appointment_form.html', {'form': form, 'action': 'Book'})


@login_required
def appointment_edit(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, user=request.user)
    if appt.status in ('confirmed', 'completed'):
        messages.warning(request, "This appointment cannot be edited.")
        return redirect('mentalapp:appointment_list')
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appt)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment updated successfully.")
            return redirect('mentalapp:appointment_list')
    else:
        form = AppointmentForm(instance=appt)
    return render(request, 'mentalapp/appointment_form.html', {'form': form, 'action': 'Update'})


@login_required
def appointment_cancel(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, user=request.user)
    if request.method == 'POST':
        appt.status = 'cancelled'
        appt.save()
        messages.info(request, "Your appointment has been cancelled.")
    return redirect('mentalapp:appointment_list')