from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from logs.models import MealLog

from .agents import Orchestrator, carb_audio, carb_vision
from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
)

orchestrator = Orchestrator()


class ChatSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatSessionDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):
        session = ChatSession.objects.filter(
            id=session_id, user=request.user
        ).first()
        if not session:
            return Response(status=status.HTTP_404_NOT_FOUND)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = ChatSession.objects.filter(
            id=session_id, user=request.user
        ).first()
        if not session:
            return Response(status=status.HTTP_404_NOT_FOUND)

        messages = session.messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, session_id):
        # Validate input
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_text = serializer.validated_data['message']

        # Verify session ownership
        session = ChatSession.objects.filter(
            id=session_id, user=request.user
        ).first()
        if not session:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Save user message
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=user_text,
        )

        # Build conversation history for context
        history = [
            {'role': msg.role, 'content': msg.content}
            for msg in session.messages.all()
        ]

        # Process through orchestrator
        result = orchestrator.process(user_text, history, request.user)

        # Save assistant reply with metadata
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=result.content,
            agent_used=result.agent_used,
            intent=result.intent,
        )

        # Auto-set title from first user message
        if not session.title:
            session.title = user_text[:50]
            session.save(update_fields=['title'])

        return Response(
            ChatMessageSerializer(assistant_msg).data,
            status=status.HTTP_201_CREATED,
        )


# ─── Upload endpoint (image / audio) ──────────────────────────────────
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
ALLOWED_AUDIO_TYPES = {
    'audio/webm', 'audio/mp4', 'audio/mpeg', 'audio/wav',
    'audio/ogg', 'audio/x-m4a',
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024    # 5 MB
MAX_AUDIO_BYTES = 10 * 1024 * 1024   # 10 MB


class ChatUploadView(APIView):
    """POST an image or audio clip into an existing chat session."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, session_id):
        session = ChatSession.objects.filter(
            id=session_id, user=request.user
        ).first()
        if not session:
            return Response(status=status.HTTP_404_NOT_FOUND)

        image = request.FILES.get('image')
        audio = request.FILES.get('audio')
        hint = (request.data.get('message') or '').strip()

        if not image and not audio:
            return Response({'detail': 'Provide image or audio.'}, status=400)
        if image and audio:
            return Response(
                {'detail': 'Send one of image or audio, not both.'},
                status=400,
            )

        # ── Audio branch ──────────────────────────────────────────────
        if audio:
            if audio.size > MAX_AUDIO_BYTES:
                return Response(
                    {'detail': 'Audio too large (10MB max).'}, status=400,
                )
            if audio.content_type not in ALLOWED_AUDIO_TYPES:
                return Response(
                    {'detail': f'Unsupported audio type: {audio.content_type}'},
                    status=400,
                )

            transcript = carb_audio.transcribe(audio.read(), filename=audio.name)
            if not transcript:
                return Response(
                    {'detail': 'Could not transcribe audio.'}, status=422,
                )

            # Save user message AS the transcript so the chat history is honest
            ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.USER,
                content=f'🎤 {transcript}',
            )

            history = [
                {'role': m.role, 'content': m.content}
                for m in session.messages.all()
            ]
            result = orchestrator.process(transcript, history, request.user)

            # If the orchestrator routed to carb_estimator, mark the source
            # as ai_audio (it would otherwise be ai_text from carb.py).
            if result.agent_used == 'carb_estimator':
                latest = (
                    MealLog.objects.filter(user=request.user)
                    .order_by('-id').first()
                )
                if latest and latest.carb_source == 'ai_text':
                    latest.carb_source = 'ai_audio'
                    latest.save(update_fields=['carb_source'])

            assistant_msg = ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.ASSISTANT,
                content=result.content,
                agent_used=result.agent_used,
                intent=result.intent,
            )
            _autotitle(session, transcript)
            return Response(
                ChatMessageSerializer(assistant_msg).data,
                status=status.HTTP_201_CREATED,
            )

        # ── Image branch ──────────────────────────────────────────────
        if image.size > MAX_IMAGE_BYTES:
            return Response(
                {'detail': 'Image too large (5MB max).'}, status=400,
            )
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            return Response(
                {'detail': f'Unsupported image type: {image.content_type}'},
                status=400,
            )

        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=(f'📷 [photo] {hint}' if hint else '📷 [photo]'),
        )

        reply = carb_vision.handle(
            image.read(), image.content_type, hint, request.user,
        )
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=reply,
            agent_used='carb_estimator',
            intent='food_log',
        )
        _autotitle(session, hint or 'Meal photo')
        return Response(
            ChatMessageSerializer(assistant_msg).data,
            status=status.HTTP_201_CREATED,
        )


def _autotitle(session, fallback: str) -> None:
    if not session.title:
        session.title = (fallback or 'Chat')[:50]
        session.save(update_fields=['title'])
