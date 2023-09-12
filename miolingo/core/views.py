from django.contrib.auth import get_user_model

from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from miolingo.core.models import Lesson, Training, Translation
from miolingo.core.serializers import (
    LessonSaveSerializer,
    LessonSerializer,
    StatSaveSerializer,
    TrainingCreateSerializer,
    TrainingSerializer,
    TrainingUpdateSerializer,
    TranslationSaveSerializer,
    TranslationSerializer,
    UserSaveSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewset(UpdateModelMixin, GenericViewSet):
    filter_backends = []
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # pragma: no cover
            return User.objects.none()

        return User.objects.filter(username=self.request.user.username)

    def get_serializer_class(self):
        if self.action in ["create", "partial_update", "update"]:
            return UserSaveSerializer
        else:
            return UserSerializer

    @action(detail=False)
    def me(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset())
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class TranslationViewset(ModelViewSet):
    filterset_fields = ["lang"]
    ordering_fields = ["text", "priority"]
    ordering = ["-priority"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # pragma: no cover
            return Translation.objects.none()

        return Translation.objects.filter(user=self.request.user).prefetch_related(
            "trans"
        )

    def get_serializer_class(self):
        if self.action in ["create", "partial_update", "update"]:
            return TranslationSaveSerializer
        else:
            return TranslationSerializer


class LessonViewset(ModelViewSet):
    filterset_fields = ["is_active"]
    ordering_fields = ["priority", "name"]
    ordering = ["-priority", "name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # pragma: no cover
            return Lesson.objects.none()

        return Lesson.objects.filter(user=self.request.user).prefetch_related(
            "translations__trans"
        )

    def get_serializer_class(self):
        if self.action in ["create", "partial_update", "update"]:
            return LessonSaveSerializer
        else:
            return LessonSerializer


class TrainingViewset(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # pragma: no cover
            return Training.objects.none()

        return Training.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return TrainingCreateSerializer

        elif self.action in ["partial_update", "update"]:
            return TrainingUpdateSerializer

        else:  # pragma: no cover
            return TrainingSerializer


class StatViewset(CreateModelMixin, GenericViewSet):
    def get_serializer_class(self):
        return StatSaveSerializer
