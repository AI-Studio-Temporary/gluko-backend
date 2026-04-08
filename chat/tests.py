from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .agents.orchestrator import AgentResult
from .agents.safety import check_safety
from .models import ChatSession, ChatMessage


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

    @patch('chat.views.orchestrator.process')
    def test_send_message(self, mock_process):
        mock_process.return_value = AgentResult(
            content='Here is some info about blood sugar.',
            agent_used='tutor',
            intent='diabetes_question',
        )
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages/',
            {'message': 'What is a normal blood sugar level?'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['role'], 'assistant')
        self.assertEqual(data['agent_used'], 'tutor')
        self.assertEqual(data['intent'], 'diabetes_question')
        self.assertIn('blood sugar', data['content'])
        mock_process.assert_called_once()
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

    @patch('chat.views.orchestrator.process')
    def test_get_history_with_messages(self, mock_process):
        mock_process.return_value = AgentResult('Reply 1', 'tutor', 'diabetes_question')
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

    @patch('chat.views.orchestrator.process')
    def test_agent_metadata_in_response(self, mock_process):
        mock_process.return_value = AgentResult(
            content='Glucose logged: 120 mg/dL',
            agent_used='log_agent',
            intent='glucose_log',
            confidence=0.95,
        )
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages/',
            {'message': 'My glucose is 120'},
        )
        data = response.json()
        self.assertEqual(data['agent_used'], 'log_agent')
        self.assertEqual(data['intent'], 'glucose_log')


# ── Safety Gate Tests ────────────────────────────────────────


class SafetyGateTests(APITestCase):
    """Test the enhanced safety gate."""

    def test_emergency_keyword_detected(self):
        result = check_safety('someone is unconscious')
        self.assertIsNotNone(result)
        self.assertTrue(result['is_emergency'])
        self.assertEqual(result['severity'], 'CRITICAL')

    def test_normal_message_passes(self):
        result = check_safety('What is a good breakfast for diabetics?')
        self.assertIsNone(result)

    def test_case_insensitive(self):
        result = check_safety('CALL 911 NOW')
        self.assertIsNotNone(result)

    def test_severe_hypo_by_value(self):
        result = check_safety('my glucose is 45 and I feel shaky')
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'severe_hypoglycemia')
        self.assertEqual(result['severity'], 'CRITICAL')

    def test_severe_hyper_by_value(self):
        result = check_safety('blood sugar is 450')
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'severe_hyperglycemia')

    def test_normal_glucose_passes(self):
        result = check_safety('my glucose is 120')
        self.assertIsNone(result)

    def test_dka_detected(self):
        result = check_safety('I think I have DKA')
        self.assertIsNotNone(result)

    def test_mental_health_detected(self):
        result = check_safety('I feel suicidal')
        self.assertIsNotNone(result)
        self.assertEqual(result['severity'], 'CRITICAL')

    @patch('chat.views.orchestrator.process')
    def test_safety_gate_in_chat_flow(self, mock_process):
        """Safety gate should be triggered before orchestrator in the full flow."""
        # The orchestrator itself handles safety, so we test it directly
        from .agents import Orchestrator
        orch = Orchestrator()
        user = User.objects.create_user(username='safe@test.com', email='safe@test.com', password='Pass1234!')
        result = orch.process('someone is having a seizure', [], user)
        self.assertEqual(result.agent_used, 'safety_gate')
        self.assertEqual(result.intent, 'emergency')
