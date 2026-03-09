from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterViewTests(APITestCase):
    url = '/api/auth/register/'

    def _valid_payload(self, email='test@example.com'):
        return {'email': email, 'password': 'StrongPass1!', 'password_confirm': 'StrongPass1!'}

    def test_register_success(self):
        response = self.client.post(self.url, self._valid_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('user', data)
        self.assertIn('tokens', data)
        self.assertIn('access', data['tokens'])
        self.assertIn('refresh', data['tokens'])
        self.assertEqual(data['user']['email'], 'test@example.com')

    def test_register_duplicate_email(self):
        self.client.post(self.url, self._valid_payload())
        response = self.client.post(self.url, self._valid_payload())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_password_confirm(self):
        payload = {'email': 'a@example.com', 'password': 'StrongPass1!'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        payload = {'email': 'b@example.com', 'password': 'StrongPass1!', 'password_confirm': 'Different1!'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTests(APITestCase):
    url = '/api/auth/login/'

    def setUp(self):
        User.objects.create_user(username='user@example.com', email='user@example.com', password='Pass1234!')

    def test_login_success(self):
        response = self.client.post(self.url, {'email': 'user@example.com', 'password': 'Pass1234!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)

    def test_login_wrong_password(self):
        response = self.client.post(self.url, {'email': 'user@example.com', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RefreshViewTests(APITestCase):
    url = '/api/auth/refresh/'

    def setUp(self):
        user = User.objects.create_user(username='r@example.com', email='r@example.com', password='Pass1234!')
        self.refresh = str(RefreshToken.for_user(user))

    def test_refresh_success(self):
        response = self.client.post(self.url, {'refresh': self.refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.json())


class LogoutViewTests(APITestCase):
    url = '/api/auth/logout/'

    def setUp(self):
        self.user = User.objects.create_user(username='lo@example.com', email='lo@example.com', password='Pass1234!')
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

    def test_logout_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_logout_blacklists_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.client.post(self.url, {'refresh': self.refresh_token})
        # Attempt to use the blacklisted refresh token
        response = self.client.post('/api/auth/refresh/', {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post(self.url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
