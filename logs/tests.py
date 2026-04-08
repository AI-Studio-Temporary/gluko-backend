from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import GlucoseLog, InsulinLog, MealLog


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
