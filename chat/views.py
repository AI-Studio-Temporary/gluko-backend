from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .agent import get_tutor_response
from .models import ChatSession, ChatMessage
from .safety import check_safety
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
)


class ChatSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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

        # Safety gate
        emergency = check_safety(user_text)
        if emergency:
            assistant_msg = ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.ASSISTANT,
                content=emergency,
            )
            return Response(
                ChatMessageSerializer(assistant_msg).data,
                status=status.HTTP_201_CREATED,
            )

        # Build conversation history and call tutor
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages.all()
        ]
        profile_context = ''
        try:
            profile_context = request.user.profile.to_context_string()
        except Exception:
            pass
        reply = get_tutor_response(history, profile_context)

        # Save assistant reply
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=reply,
        )

        # Auto-set title from first user message
        if not session.title:
            session.title = user_text[:50]
            session.save(update_fields=['title'])

        return Response(
            ChatMessageSerializer(assistant_msg).data,
            status=status.HTTP_201_CREATED,
        )
