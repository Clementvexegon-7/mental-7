# ================================================================
#  mentalapp/tests.py  — Basic test suite
# ================================================================

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Mood, JournalEntry, Checklist, UserProfile, Appointment


# ── Helper ────────────────────────────────────────────────────
def make_user(username='testuser', password='TestPass123!'):
    user = User.objects.create_user(username=username, password=password, email=f'{username}@test.com')
    return user


# ── Model Tests ───────────────────────────────────────────────
class MoodModelTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_mood_creation(self):
        mood = Mood.objects.create(user=self.user, mood_score=7)
        self.assertEqual(mood.mood_score, 7)
        self.assertEqual(mood.score, 7)          # property alias
        self.assertEqual(mood.label, 'Good')     # property alias
        self.assertEqual(mood.mood_emoji, '😊')

    def test_mood_str(self):
        mood = Mood.objects.create(user=self.user, mood_score=5)
        self.assertIn('testuser', str(mood))

    def test_mood_unique_per_day(self):
        Mood.objects.create(user=self.user, mood_score=5)
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Mood.objects.create(user=self.user, mood_score=7, date=timezone.now().date())


class ChecklistModelTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_completion_score_empty(self):
        cl = Checklist.objects.create(user=self.user)
        self.assertEqual(cl.completion_score, 0)
        self.assertEqual(cl.completion_percent, 0)
        self.assertEqual(cl.emotional_label, 'Start somewhere 🌱')

    def test_completion_score_full(self):
        cl = Checklist.objects.create(
            user=self.user,
            slept_well=True, exercised=True, ate_well=True, stayed_hydrated=True,
            meditated=True, journaled=True, limited_screens=True,
            connected_others=True, set_boundaries=True,
            spent_time_outside=True, expressed_gratitude=True,
        )
        self.assertEqual(cl.completion_score, 11)
        self.assertEqual(cl.completion_percent, 100)
        self.assertEqual(cl.emotional_label, 'Outstanding! 🌟')

    def test_completion_score_partial(self):
        cl = Checklist.objects.create(user=self.user, slept_well=True, exercised=True, ate_well=True)
        self.assertEqual(cl.completion_score, 3)
        self.assertIn('Tough day', cl.emotional_label)


class JournalEntryModelTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_journal_creation(self):
        entry = JournalEntry.objects.create(user=self.user, title='Test', content='Hello world')
        self.assertEqual(str(entry), 'testuser — Test')
        self.assertTrue(entry.is_private)

    def test_short_content(self):
        long = 'A' * 200
        entry = JournalEntry.objects.create(user=self.user, title='T', content=long)
        self.assertTrue(entry.short_content().endswith('…'))


class UserProfileModelTest(TestCase):
    def test_profile_auto_created(self):
        user = make_user('profiletest')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())


# ── View Tests ────────────────────────────────────────────────
class PublicViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view(self):
        response = self.client.get(reverse('mentalapp:home'))
        self.assertEqual(response.status_code, 200)

    def test_about_view(self):
        response = self.client.get(reverse('mentalapp:about'))
        self.assertEqual(response.status_code, 200)

    def test_conditions_view(self):
        response = self.client.get(reverse('mentalapp:conditions'))
        self.assertEqual(response.status_code, 200)

    def test_signs_view(self):
        response = self.client.get(reverse('mentalapp:signs'))
        self.assertEqual(response.status_code, 200)

    def test_prevention_view(self):
        response = self.client.get(reverse('mentalapp:prevention'))
        self.assertEqual(response.status_code, 200)

    def test_resources_view(self):
        response = self.client.get(reverse('mentalapp:resources'))
        self.assertEqual(response.status_code, 200)

    def test_mwendo_page(self):
        response = self.client.get(reverse('mentalapp:mwendo_page'))
        self.assertEqual(response.status_code, 200)

    def test_register_get(self):
        response = self.client.get(reverse('mentalapp:register'))
        self.assertEqual(response.status_code, 200)

    def test_login_get(self):
        response = self.client.get(reverse('mentalapp:login'))
        self.assertEqual(response.status_code, 200)


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user   = make_user()

    def test_register_redirects_if_logged_in(self):
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('mentalapp:register'))
        self.assertRedirects(response, reverse('mentalapp:home'))

    def test_login_success(self):
        response = self.client.post(reverse('mentalapp:login'), {
            'username': 'testuser', 'password': 'TestPass123!'
        })
        self.assertRedirects(response, reverse('mentalapp:home'))

    def test_login_failure(self):
        response = self.client.post(reverse('mentalapp:login'), {
            'username': 'testuser', 'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid' in str(m) for m in messages))


class ProtectedViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user   = make_user()
        self.client.login(username='testuser', password='TestPass123!')

    def test_dashboard_authenticated(self):
        response = self.client.get(reverse('mentalapp:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_unauthenticated_redirects(self):
        self.client.logout()
        response = self.client.get(reverse('mentalapp:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_mood_list(self):
        response = self.client.get(reverse('mentalapp:mood_list'))
        self.assertEqual(response.status_code, 200)

    def test_mood_create_get(self):
        response = self.client.get(reverse('mentalapp:mood_create'))
        self.assertEqual(response.status_code, 200)

    def test_mood_create_post(self):
        response = self.client.post(reverse('mentalapp:mood_create'), {
            'mood_score': 7, 'notes': 'Feeling good', 'date': timezone.now().date()
        })
        self.assertRedirects(response, reverse('mentalapp:mood_list'))
        self.assertTrue(Mood.objects.filter(user=self.user, mood_score=7).exists())

    def test_checklist_today(self):
        response = self.client.get(reverse('mentalapp:checklist_today'))
        self.assertEqual(response.status_code, 200)

    def test_journal_list(self):
        response = self.client.get(reverse('mentalapp:journal_list'))
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        response = self.client.get(reverse('mentalapp:profile'))
        self.assertEqual(response.status_code, 200)


# ── Mwendo Chat API Tests ─────────────────────────────────────
class MwendoChatAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_method_rejected(self):
        response = self.client.get(reverse('mentalapp:mwendo_chat'))
        self.assertEqual(response.status_code, 405)

    def test_post_anxiety(self):
        response = self.client.post(
            reverse('mentalapp:mwendo_chat'),
            data='{"message": "I feel very anxious today"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('reply', data)
        self.assertIn('Anxiety', data['reply'])

    def test_post_crisis_detected(self):
        response = self.client.post(
            reverse('mentalapp:mwendo_chat'),
            data='{"message": "I want to die"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('crisis', False))
        self.assertIn('0722 178 177', data['reply'])

    def test_post_empty_message(self):
        response = self.client.post(
            reverse('mentalapp:mwendo_chat'),
            data='{"message": ""}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_post_invalid_json(self):
        response = self.client.post(
            reverse('mentalapp:mwendo_chat'),
            data='not valid json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_positive_response(self):
        response = self.client.post(
            reverse('mentalapp:mwendo_chat'),
            data='{"message": "I feel great today!"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('reply', data)


# ── Dashboard Context Tests ───────────────────────────────────
class DashboardContextTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user   = make_user()
        self.client.login(username='testuser', password='TestPass123!')

    def test_dashboard_has_insight(self):
        response = self.client.get(reverse('mentalapp:dashboard'))
        self.assertIn('insight', response.context)
        self.assertIn('streak', response.context)
        self.assertIn('today_score', response.context)

    def test_streak_increments_with_checklist(self):
        Checklist.objects.create(
            user=self.user, date=timezone.now().date(),
            slept_well=True, exercised=True, ate_well=True,
        )
        response = self.client.get(reverse('mentalapp:dashboard'))
        self.assertGreaterEqual(response.context['streak'], 1)