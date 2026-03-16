from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ChatSession, ChatMessage
from .safety import check_safety, EMERGENCY_RESPONSE


class ChatSessionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='chat@example.com', email='chat@example.com', password='Pass1234!'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_create_session(self):
        response = self.client.post('/api/chat/sessions/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatSession.objects.count(), 1)

    def test_create_session_with_title(self):
        response = self.client.post('/api/chat/sessions/', {'title': 'My Chat'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['title'], 'My Chat')

    def test_list_own_sessions(self):
        ChatSession.objects.create(user=self.user, title='Session 1')
        ChatSession.objects.create(user=self.user, title='Session 2')
        other_user = User.objects.create_user(
            username='other@example.com', email='other@example.com', password='Pass1234!'
        )
        ChatSession.objects.create(user=other_user, title='Other Session')

        response = self.client.get('/api/chat/sessions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_unauthenticated_rejected(self):
        self.client.credentials()
        response = self.client.post('/api/chat/sessions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatMessageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='msg@example.com', email='msg@example.com', password='Pass1234!'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.session = ChatSession.objects.create(user=self.user)

    @patch('chat.views.get_tutor_response', return_value='Here is some info about blood sugar.')
    def test_send_message(self, mock_tutor):
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages/',
            {'message': 'What is a normal blood sugar level?'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['role'], 'assistant')
        self.assertIn('blood sugar', response.json()['content'])
        mock_tutor.assert_called_once()
        # Check auto-title
        self.session.refresh_from_db()
        self.assertEqual(self.session.title, 'What is a normal blood sugar level?')

    def test_empty_message_rejected(self):
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages/',
            {'message': ''},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_empty_history(self):
        response = self.client.get(f'/api/chat/sessions/{self.session.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @patch('chat.views.get_tutor_response', return_value='Reply 1')
    def test_get_history_with_messages(self, mock_tutor):
        self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages/',
            {'message': 'Hello'},
        )
        response = self.client.get(f'/api/chat/sessions/{self.session.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = response.json()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'user')
        self.assertEqual(messages[1]['role'], 'assistant')

    def test_other_users_session_returns_404(self):
        other_user = User.objects.create_user(
            username='other2@example.com', email='other2@example.com', password='Pass1234!'
        )
        other_session = ChatSession.objects.create(user=other_user)
        response = self.client.get(f'/api/chat/sessions/{other_session.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_session_returns_404(self):
        response = self.client.get('/api/chat/sessions/9999/messages/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SafetyGateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='safe@example.com', email='safe@example.com', password='Pass1234!'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.session = ChatSession.objects.create(user=self.user)

    @patch('chat.views.get_tutor_response')
    def test_emergency_keyword_triggers_safety(self, mock_tutor):
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages/',
            {'message': 'My friend is having a seizure what do I do'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('emergency', response.json()['content'].lower())
        mock_tutor.assert_not_called()

    @patch('chat.views.get_tutor_response', return_value='Normal response')
    def test_normal_message_passes_through(self, mock_tutor):
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages/',
            {'message': 'What foods are good for managing diabetes?'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['content'], 'Normal response')
        mock_tutor.assert_called_once()

    @patch('chat.views.get_tutor_response')
    def test_case_insensitive_matching(self, mock_tutor):
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages/',
            {'message': 'This is an EMERGENCY please help'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('emergency', response.json()['content'].lower())
        mock_tutor.assert_not_called()


class SafetyGateUnitTests(APITestCase):
    def test_emergency_keyword_returns_response(self):
        result = check_safety('someone is unconscious')
        self.assertEqual(result, EMERGENCY_RESPONSE)

    def test_normal_message_returns_none(self):
        result = check_safety('What is a good breakfast for diabetics?')
        self.assertIsNone(result)

    def test_case_insensitive(self):
        result = check_safety('CALL 911 NOW')
        self.assertEqual(result, EMERGENCY_RESPONSE)

    def test_diabetic_coma_detected(self):
        result = check_safety('I think this is a diabetic coma')
        self.assertEqual(result, EMERGENCY_RESPONSE)

    def test_severe_hypoglycemia_detected(self):
        result = check_safety('signs of severe hypoglycemia')
        self.assertEqual(result, EMERGENCY_RESPONSE)
