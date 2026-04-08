from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile

from .models import BolusCalculation, GlucoseLog, InsulinLog, MealLog, SportLog


class LogTestMixin:
    """Shared helpers for log test classes."""

    def _auth(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    def _create_users(self):
        self.user = User.objects.create_user(
            username='log@example.com', email='log@example.com', password='Pass1234!',
        )
        self.other_user = User.objects.create_user(
            username='other@example.com', email='other@example.com', password='Pass1234!',
        )
        self._auth(self.user)


# ── Glucose ──────────────────────────────────────────────────


class GlucoseLogTests(LogTestMixin, APITestCase):
    url = '/api/logs/glucose/'

    def setUp(self):
        self._create_users()

    def test_create_glucose_log(self):
        payload = {'value_mgdl': 120, 'measurement_context': 'fasting'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GlucoseLog.objects.count(), 1)
        self.assertEqual(GlucoseLog.objects.first().user, self.user)

    def test_list_own_glucose_logs(self):
        GlucoseLog.objects.create(user=self.user, value_mgdl=100)
        GlucoseLog.objects.create(user=self.user, value_mgdl=130)
        GlucoseLog.objects.create(user=self.other_user, value_mgdl=200)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_list_ordered_by_logged_at_desc(self):
        now = timezone.now()
        GlucoseLog.objects.create(user=self.user, value_mgdl=100, logged_at=now - timedelta(hours=2))
        GlucoseLog.objects.create(user=self.user, value_mgdl=200, logged_at=now)

        response = self.client.get(self.url)
        values = [entry['value_mgdl'] for entry in response.json()]
        self.assertEqual(values, [200, 100])

    def test_delete_glucose_log(self):
        log = GlucoseLog.objects.create(user=self.user, value_mgdl=100)
        response = self.client.delete(f'{self.url}{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(GlucoseLog.objects.count(), 0)

    def test_cant_delete_others_glucose_log(self):
        log = GlucoseLog.objects.create(user=self.other_user, value_mgdl=100)
        response = self.client.delete(f'{self.url}{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_date_filter(self):
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        GlucoseLog.objects.create(user=self.user, value_mgdl=100, logged_at=now)
        GlucoseLog.objects.create(user=self.user, value_mgdl=200, logged_at=yesterday)

        response = self.client.get(self.url, {'date': now.strftime('%Y-%m-%d')})
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['value_mgdl'], 100)


# ── Insulin ──────────────────────────────────────────────────


class InsulinLogTests(LogTestMixin, APITestCase):
    url = '/api/logs/insulin/'

    def setUp(self):
        self._create_users()

    def test_create_insulin_log(self):
        payload = {'units': '4.50', 'insulin_type': 'bolus'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InsulinLog.objects.count(), 1)
        self.assertEqual(InsulinLog.objects.first().user, self.user)

    def test_list_own_insulin_logs(self):
        InsulinLog.objects.create(user=self.user, units=4, insulin_type='bolus')
        InsulinLog.objects.create(user=self.user, units=20, insulin_type='basal')
        InsulinLog.objects.create(user=self.other_user, units=5, insulin_type='bolus')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_delete_insulin_log(self):
        log = InsulinLog.objects.create(user=self.user, units=4, insulin_type='bolus')
        response = self.client.delete(f'{self.url}{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cant_delete_others_insulin_log(self):
        log = InsulinLog.objects.create(user=self.other_user, units=4, insulin_type='bolus')
        response = self.client.delete(f'{self.url}{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_date_filter(self):
        now = timezone.now()
        InsulinLog.objects.create(user=self.user, units=4, insulin_type='bolus', logged_at=now)
        InsulinLog.objects.create(
            user=self.user, units=20, insulin_type='basal', logged_at=now - timedelta(days=1),
        )

        response = self.client.get(self.url, {'date': now.strftime('%Y-%m-%d')})
        self.assertEqual(len(response.json()), 1)


# ── Meal ─────────────────────────────────────────────────────


class MealLogTests(LogTestMixin, APITestCase):
    url = '/api/logs/meals/'

    def setUp(self):
        self._create_users()

    def test_create_meal_log(self):
        payload = {
            'description': 'Chicken sandwich and apple',
            'estimated_carbs': '55.00',
            'meal_type': 'lunch',
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MealLog.objects.count(), 1)
        self.assertEqual(MealLog.objects.first().user, self.user)

    def test_create_meal_log_without_carbs(self):
        payload = {'description': 'Mystery meal'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(MealLog.objects.first().estimated_carbs)

    def test_list_own_meal_logs(self):
        MealLog.objects.create(user=self.user, description='Breakfast')
        MealLog.objects.create(user=self.user, description='Lunch')
        MealLog.objects.create(user=self.other_user, description='Other meal')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_delete_meal_log(self):
        log = MealLog.objects.create(user=self.user, description='Snack')
        response = self.client.delete(f'{self.url}{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cant_delete_others_meal_log(self):
        log = MealLog.objects.create(user=self.other_user, description='Snack')
        response = self.client.delete(f'{self.url}{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_date_filter(self):
        now = timezone.now()
        MealLog.objects.create(user=self.user, description='Today', logged_at=now)
        MealLog.objects.create(
            user=self.user, description='Yesterday', logged_at=now - timedelta(days=1),
        )

        response = self.client.get(self.url, {'date': now.strftime('%Y-%m-%d')})
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['description'], 'Today')


# ── Auth ─────────────────────────────────────────────────────


class UnauthenticatedTests(APITestCase):
    def test_glucose_requires_auth(self):
        self.assertEqual(self.client.get('/api/logs/glucose/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_insulin_requires_auth(self):
        self.assertEqual(self.client.get('/api/logs/insulin/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_meals_requires_auth(self):
        self.assertEqual(self.client.get('/api/logs/meals/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sport_requires_auth(self):
        self.assertEqual(self.client.get('/api/logs/sport/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bolus_calculate_requires_auth(self):
        self.assertEqual(self.client.post('/api/logs/bolus/calculate/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bolus_history_requires_auth(self):
        self.assertEqual(self.client.get('/api/logs/bolus/history/').status_code, status.HTTP_401_UNAUTHORIZED)


# ── Sport ────────────────────────────────────────────────────


class SportLogTests(LogTestMixin, APITestCase):
    url = '/api/logs/sport/'

    def setUp(self):
        self._create_users()

    def test_create_sport_log(self):
        payload = {'activity_type': 'running', 'duration_min': 30, 'intensity': 'moderate'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SportLog.objects.count(), 1)
        self.assertEqual(SportLog.objects.first().user, self.user)

    def test_create_sport_log_with_glucose(self):
        payload = {
            'activity_type': 'cycling', 'duration_min': 60, 'intensity': 'high',
            'glucose_before': 120, 'glucose_after': 95,
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        log = SportLog.objects.first()
        self.assertEqual(log.glucose_before, 120)
        self.assertEqual(log.glucose_after, 95)

    def test_list_own_sport_logs(self):
        SportLog.objects.create(user=self.user, activity_type='running', duration_min=30)
        SportLog.objects.create(user=self.other_user, activity_type='swimming', duration_min=45)

        response = self.client.get(self.url)
        self.assertEqual(len(response.json()), 1)

    def test_delete_sport_log(self):
        log = SportLog.objects.create(user=self.user, activity_type='yoga', duration_min=20)
        response = self.client.delete(f'{self.url}{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cant_delete_others_sport_log(self):
        log = SportLog.objects.create(user=self.other_user, activity_type='yoga', duration_min=20)
        response = self.client.delete(f'{self.url}{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_date_filter(self):
        now = timezone.now()
        SportLog.objects.create(user=self.user, activity_type='run', duration_min=30, logged_at=now)
        SportLog.objects.create(
            user=self.user, activity_type='swim', duration_min=45, logged_at=now - timedelta(days=1),
        )
        response = self.client.get(self.url, {'date': now.strftime('%Y-%m-%d')})
        self.assertEqual(len(response.json()), 1)


# ── Bolus Calculator ────────────────────────────────────────


class BolusCalculateTests(LogTestMixin, APITestCase):
    url = '/api/logs/bolus/calculate/'
    history_url = '/api/logs/bolus/history/'

    def setUp(self):
        self._create_users()

    def _setup_profile(self, user=None):
        user = user or self.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.insulin_to_carb_ratio = 10
        profile.insulin_sensitivity_factor = 2.5
        profile.target_bg_min = 5.5
        profile.on_insulin = True
        profile.save()
        return profile

    def test_bolus_calculate_happy_path(self):
        self._setup_profile()
        payload = {'carbohydrates_g': '60.00', 'current_glucose': '9.0'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        # meal_dose = 60 / 10 = 6.0
        self.assertEqual(data['meal_dose'], 6.0)
        # correction_dose = (9.0 - 5.5) / 2.5 = 1.4
        self.assertEqual(data['correction_dose'], 1.4)
        # total = 6.0 + 1.4 = 7.4
        self.assertEqual(data['total_dose'], 7.4)
        self.assertIn('formula', data)
        self.assertIn('disclaimer', data)

        # Check saved to DB
        self.assertEqual(BolusCalculation.objects.count(), 1)

    def test_no_correction_when_at_target(self):
        self._setup_profile()
        payload = {'carbohydrates_g': '40.00', 'current_glucose': '5.0'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['meal_dose'], 4.0)
        self.assertEqual(data['correction_dose'], 0.0)
        self.assertEqual(data['total_dose'], 4.0)

    def test_missing_profile_returns_400(self):
        # No profile at all
        payload = {'carbohydrates_g': '50.00', 'current_glucose': '7.0'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_icr_isf_returns_400(self):
        # Profile exists but ICR/ISF not set
        UserProfile.objects.get_or_create(user=self.user)
        payload = {'carbohydrates_g': '50.00', 'current_glucose': '7.0'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bolus_history(self):
        self._setup_profile()
        self.client.post(self.url, {'carbohydrates_g': '60', 'current_glucose': '8.0'})
        self.client.post(self.url, {'carbohydrates_g': '30', 'current_glucose': '6.0'})

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_bolus_history_user_isolation(self):
        self._setup_profile()
        self._setup_profile(self.other_user)
        self.client.post(self.url, {'carbohydrates_g': '60', 'current_glucose': '8.0'})

        # Switch to other user
        self._auth(self.other_user)
        self.client.post(self.url, {'carbohydrates_g': '30', 'current_glucose': '7.0'})

        # Each user sees only their own
        response = self.client.get(self.history_url)
        self.assertEqual(len(response.json()), 1)

        self._auth(self.user)
        response = self.client.get(self.history_url)
        self.assertEqual(len(response.json()), 1)
