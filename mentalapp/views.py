# ================================================================
#  mentalapp/views.py  — FINAL UPGRADED VERSION
# ================================================================

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import (
    Mood, JournalEntry, SavedResource, Checklist,
    UserProfile, ContactMessage, Appointment,
)
from .forms import (
    UserRegisterForm, UserProfileForm, LoginForm,
    MoodForm, JournalForm, ChecklistForm,
    SavedResourceForm, ContactMessageForm, AppointmentForm,
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

def mwendo_page(request):
    """Dedicated full-page AI companion chat."""
    return render(request, 'mentalapp/mwendo_page.html')

def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            if request.user.is_authenticated:
                msg.user = request.user
            msg.save()
            messages.success(request, "Your message has been sent! We'll reply within 24 hours.")
            return redirect('mentalapp:contact')
    else:
        form = ContactMessageForm()
    return render(request, 'mentalapp/contact.html', {'form': form})


# ── AUTHENTICATION ─────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('mentalapp:home')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to MindWell, {user.first_name or user.username}! 🌿")
            return redirect('mentalapp:home')
    else:
        form = UserRegisterForm()
    return render(request, 'mentalapp/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('mentalapp:home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url if next_url else 'mentalapp:home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
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

    # ── Today's score ─────────────────────────────────────────
    today_score = today_checklist.completion_score if today_checklist else 0

    # ── AI Insight ────────────────────────────────────────────
    if today_score >= 9:
        insight = "🌟 Outstanding day — you've completed almost every habit. Your mental health is thriving right now."
    elif today_score >= 7:
        insight = "😊 Strong day! You're building real momentum. Try adding one more habit to push for your best."
    elif today_score >= 5:
        insight = "🙂 You're doing okay today. Consistency over perfection — every habit logged is progress."
    elif today_score >= 2:
        insight = "💙 It's been a tough day. That's okay — even one habit is a win. Start with something small right now."
    elif today_checklist:
        insight = "🌱 You opened your checklist — that's step one. Try ticking just one habit to start your momentum."
    else:
        insight = "🌿 You haven't logged today yet. Your wellbeing matters — start with your checklist to unlock today's insight."

    # ── Mood-based insight upgrade ────────────────────────────
    all_moods = list(Mood.objects.filter(user=request.user).order_by('-date')[:7].values_list('mood_score', flat=True))
    if all_moods:
        avg = sum(all_moods) / len(all_moods)
        recent3 = all_moods[:3]
        if len(recent3) == 3 and all(s <= 3 for s in recent3):
            insight = "💙 You've had a difficult emotional pattern for the past few days. Please consider reaching out — to Mwendo, a friend, or a professional."
        elif avg >= 7:
            insight = f"🌟 Your average mood this week is {avg:.1f}/10 — you're genuinely doing well. " + insight

    # ── Streak ───────────────────────────────────────────────
    streak = 0
    check_date = today
    while True:
        cl = Checklist.objects.filter(user=request.user, date=check_date).first()
        if cl and cl.completion_score >= 3:
            streak += 1
            check_date -= timezone.timedelta(days=1)
        else:
            break

    # ── Smart notification ────────────────────────────────────
    notification = None
    if not today_checklist:
        notification = "📋 You haven't filled your checklist today. Small habits compound into big change."
    elif today_score < 3:
        notification = "💙 Your score is low today — consider booking a session or talking to Mwendo."
    elif streak >= 7:
        notification = f"🔥 Amazing! You're on a {streak}-day streak. You're building something real."

    context = {
        'recent_moods':          recent_moods,
        'recent_journals':       recent_journals,
        'today_checklist':       today_checklist,
        'today':                 today,
        'upcoming_appointments': upcoming_appointments,
        'today_score':           today_score,
        'insight':               insight,
        'streak':                streak,
        'notification':          notification,
    }
    return render(request, 'mentalapp/dashboard.html', context)


# ── MWENDO AI CHAT ENDPOINT ────────────────────────────────────
@require_POST
def mwendo_chat(request):
    """
    Context-aware Mwendo AI endpoint.
    POST /mwendo-chat/  { "message": "...", "history": [...] }
    Returns JSON: { "reply", "quick", "action", "redirect", "crisis" }
    """
    try:
        body    = json.loads(request.body)
        message = body.get('message', '').strip()[:500]
        history = body.get('history', [])[-6:]
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    low = message.lower()

    # ── User context ─────────────────────────────────────────
    user_context = {}
    if request.user.is_authenticated:
        recent_moods = list(
            Mood.objects.filter(user=request.user)
            .order_by('-date')[:5]
            .values('mood_score', 'date')
        )
        recent_journals = list(
            JournalEntry.objects.filter(user=request.user)
            .order_by('-created_at')[:3]
            .values('title', 'created_at')
        )
        user_context = {
            'name':     request.user.get_short_name() or request.user.username,
            'moods':    recent_moods,
            'journals': recent_journals,
        }

    name_prefix = f"{user_context.get('name', '')}, " if user_context.get('name') else ""

    mood_note = ""
    if user_context.get('moods'):
        scores = [m['mood_score'] for m in user_context['moods'] if m.get('mood_score')]
        if scores:
            avg = sum(scores) / len(scores)
            if avg <= 3:
                mood_note = "I can see from your recent check-ins that things have been heavy lately. "
            elif avg >= 7:
                mood_note = "Your recent mood logs show you've been doing better — that matters. "

    # ── Crisis (highest priority) ─────────────────────────────
    if any(kw in low for kw in ['crisis','suicid','kill','harm','hurt myself','end it','die','want to die','give up','giving up','no reason to live','not worth living']):
        return JsonResponse({
            'reply':    f"{name_prefix}You matter deeply. Please reach out right now — a real person is ready to listen:\n\n🆘 **Befrienders Kenya: 0722 178 177** (24/7 · Free)\n📍 Mathari Hospital: **+254 20 2724069**\n🚑 Emergency: **999 / 112**\n\nI'm staying right here with you. You are not alone.",
            'quick':    ['Call 0722 178 177', "I'm scared but okay", 'Stay with me', '🧘 Help me breathe'],
            'action':   None, 'redirect': None, 'crisis': True,
        })

    # ── Anxiety ───────────────────────────────────────────────
    if any(kw in low for kw in ['anxi','panic','worry','stressed','overwhelm','scared','fear']):
        return JsonResponse({
            'reply':  f"{mood_note}Anxiety is real, and it can feel relentless. 💙 Your nervous system is trying to protect you — it's just being a little too enthusiastic right now.\n\nLet's slow things down together. Would a 4-minute breathing exercise help?",
            'quick':  ['🧘 Yes, let\'s breathe', 'Learn about anxiety', 'Tell me more', '🆘 I need crisis support'],
            'action': None, 'redirect': None,
        })

    # ── Sadness / Depression ──────────────────────────────────
    if any(kw in low for kw in ['sad','depress','cry','hopeless','empty','alone','lonely','worthless','numb']):
        return JsonResponse({
            'reply':  f"{mood_note}Thank you for trusting me with this. 💚 {name_prefix}Sadness doesn't mean weakness — it means something hurts, and that hurt deserves care.\n\nYou reached out today. That's not nothing — that's everything. Can I ask — are you safe right now?",
            'quick':  ["Yes, I'm safe", 'I need crisis support', 'Find support near me', '🧘 Help me breathe'],
            'action': None, 'redirect': None,
        })

    # ── Exhaustion ────────────────────────────────────────────
    if any(kw in low for kw in ['tired','exhaust','burnout','no energy','drain','sleep','worn out']):
        return JsonResponse({
            'reply':  f"Your body and mind are sending you a signal. 🌙 {mood_note}Rest is not giving up — it's maintenance for the most important thing you own: yourself.",
            'quick':  ['Self-care guide', '🧘 Try breathing', 'Tell me more', 'Find resources'],
            'action': None, 'redirect': None,
        })

    # ── Anger ─────────────────────────────────────────────────
    if any(kw in low for kw in ['angry','mad','frustrated','rage','annoyed','furious']):
        return JsonResponse({
            'reply':  f"Frustration usually means something genuinely matters to you. 🔥 That's not a character flaw — it's information.\n\nWhat's been weighing on you most?",
            'quick':  ['Work / school pressure', 'Relationships', 'Feeling unheard', 'Everything at once'],
            'action': None, 'redirect': None,
        })

    # ── Breathing ─────────────────────────────────────────────
    if any(kw in low for kw in ['breath','breathe','breathing','calm down','relax']):
        return JsonResponse({
            'reply': "Let's breathe together. 🌿 Box breathing — inhale 4, hold 4, exhale 6, hold 4. Starting now.",
            'quick': [], 'action': 'breathe', 'redirect': None,
        })

    # ── Resources ─────────────────────────────────────────────
    if any(kw in low for kw in ['therapist','counsellor','help','support','resource','find','doctor','hospital']):
        return JsonResponse({
            'reply':    f"There are people ready to support you. 💚 Our resources page has therapists, crisis lines, support groups, and apps.",
            'quick':    ['Open resources page', 'Crisis lines only', 'Talk more first'],
            'action':   None, 'redirect': 'resources',
        })

    # ── Positive ──────────────────────────────────────────────
    if any(kw in low for kw in ['good','great','happy','fine','okay','well','better','grateful','thankful']):
        mood_cel = " Your recent check-ins reflect that too — keep going." if user_context.get('moods') else ""
        return JsonResponse({
            'reply':  f"That genuinely makes me happy to hear. 🌟{mood_cel}\n\nWould you like to explore something today, or just check in?",
            'quick':  ['Self-care guide', 'Open dashboard', 'Prevention strategies', 'Just saying hi 😊'],
            'action': None, 'redirect': None,
        })

    # ── Journal ───────────────────────────────────────────────
    if any(kw in low for kw in ['journal','write','diary','record','track']):
        jnote = " I can see you've been journaling — that's one of the most powerful tools for mental clarity." if user_context.get('journals') else ""
        return JsonResponse({
            'reply':    f"Journaling is one of the most underrated forms of self-care.{jnote} 📖 Writing gives your thoughts somewhere to live outside your head.",
            'quick':    ['Open my journal', 'Give me a prompt', 'Tell me more'],
            'action':   None,
            'redirect': 'journal_list' if request.user.is_authenticated else None,
        })

    # ── Appointment ───────────────────────────────────────────
    if any(kw in low for kw in ['appointment','book','session','therapy','schedule']):
        return JsonResponse({
            'reply':    "Booking a session is a powerful act of self-care. 📅 Our appointment system lets you choose the type, mode, and time that works for you.",
            'quick':    ['Book an appointment', 'What session types exist?', 'I\'m not sure yet'],
            'action':   None, 'redirect': 'appointment_list',
        })

    # ── Default ───────────────────────────────────────────────
    opener = f"{mood_note}I hear you. 💚" if mood_note else "I hear you. 💚"
    return JsonResponse({
        'reply':  f"{opener} Whatever you're carrying right now — it's real, it matters, and you deserve care.\n\nWhat would feel most helpful right now?",
        'quick':  ['Find resources', 'Self-care guide', '🧘 Try breathing', 'Open dashboard'],
        'action': None, 'redirect': None,
    })


# ── MOOD TRACKER ───────────────────────────────────────────────
@login_required
def mood_list(request):
    moods = Mood.objects.filter(user=request.user).order_by('-date')

    avg_score = 0
    trend     = 'stable'
    if moods:
        scores = [m.mood_score for m in moods]
        avg_score = round(sum(scores) / len(scores), 1)
        recent5 = scores[:5]
        older5  = scores[5:10]
        if older5:
            r_avg = sum(recent5) / len(recent5)
            o_avg = sum(older5)  / len(older5)
            if r_avg - o_avg > 0.5:   trend = 'improving'
            elif o_avg - r_avg > 0.5: trend = 'declining'

    return render(request, 'mentalapp/mood_list.html', {
        'moods':     moods,
        'avg_score': avg_score,
        'trend':     trend,
    })


@login_required
def mood_create(request):
    if request.method == 'POST':
        form = MoodForm(request.POST)
        if form.is_valid():
            mood = form.save(commit=False)
            mood.user = request.user
            mood.save()
            messages.success(request, "Mood logged! 😊")
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
            messages.success(request, "Journal entry saved! 📓")
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
            score = checklist.completion_score
            if score >= 9:
                messages.success(request, "🌟 Outstanding! You've completed almost every habit today.")
            elif score >= 6:
                messages.success(request, "😊 Great work! Your checklist is looking strong today.")
            elif score >= 3:
                messages.success(request, "🙂 Checklist updated! Every habit logged is progress.")
            else:
                messages.info(request, "💙 Checklist saved. Small steps still count — keep going.")
            return redirect('mentalapp:checklist_today')
    else:
        form = ChecklistForm(instance=checklist)
    return render(request, 'mentalapp/checklist_today.html', {
        'form': form, 'checklist': checklist, 'today': today, 'created': created,
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
            messages.success(request, "Resource saved! 🔖")
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
            messages.success(request, "Profile updated! 💚")
            return redirect('mentalapp:profile')
    else:
        form = UserProfileForm(instance=profile_obj)
    return render(request, 'mentalapp/profile_edit.html', {'form': form})


# ── APPOINTMENTS ───────────────────────────────────────────────
@login_required
def appointment_list(request):
    today = timezone.now().date()
    upcoming = Appointment.objects.filter(
        user=request.user, preferred_date__gte=today
    ).exclude(status='cancelled').order_by('preferred_date', 'preferred_time')
    past = Appointment.objects.filter(
        user=request.user, preferred_date__lt=today
    ).order_by('-preferred_date')[:5]
    return render(request, 'mentalapp/appointment_list.html', {
        'appointments': upcoming,
        'past_appointments': past,
    })


@login_required
def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.user = request.user
            appt.save()
            messages.success(request, "Appointment booked! 📅 We'll confirm within 24 hours.")
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
            messages.success(request, "Appointment updated!")
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
        messages.info(request, "Appointment cancelled.")
    return redirect('mentalapp:appointment_list')