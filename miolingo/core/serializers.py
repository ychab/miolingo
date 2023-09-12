from django.contrib.auth import get_user_model
from django.utils.text import slugify

from rest_framework.fields import CurrentUserDefault, HiddenField
from rest_framework.serializers import ModelSerializer

from miolingo.core.fields import PrimaryKeyOwnerRelatedField
from miolingo.core.models import Lesson, Stat, Training, Translation
from miolingo.core.validators import (
    IsActiveLessonValidator,
    UniqueTogetherTranslationValidator,
)

User = get_user_model()


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "source_lang",
        ]


class UserSaveSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ["email", "first_name", "last_name", "source_lang"]


class TranslationLeafSerializer(ModelSerializer):
    class Meta:
        model = Translation
        fields = ["id", "lang", "text", "slug", "priority"]
        extra_kwargs = {
            "slug": {
                "read_only": True,
            },
            "priority": {
                "default": 0,
            },
        }


class TranslationSerializer(TranslationLeafSerializer):
    trans = TranslationLeafSerializer(many=True, read_only=True)

    class Meta(TranslationLeafSerializer.Meta):
        fields = TranslationLeafSerializer.Meta.fields + ["trans"]


class TranslationSaveSerializer(TranslationLeafSerializer):
    trans = TranslationLeafSerializer(many=True, required=False, allow_null=True)
    user = HiddenField(default=CurrentUserDefault())

    class Meta(TranslationLeafSerializer.Meta):
        fields = TranslationLeafSerializer.Meta.fields + ["trans", "user"]
        validators = [
            UniqueTogetherTranslationValidator(),
        ]

    def create(self, validated_data):
        trans_data = validated_data.pop("trans", [])

        instance = super().create(validated_data)

        translations = []
        for data in trans_data:
            trans, created = Translation.objects.get_or_create(
                user=instance.user,
                lang=data["lang"],
                slug=slugify(data["text"]),
                defaults={
                    "text": data["text"],
                    "priority": data["priority"],
                },
            )
            translations.append(trans)

        if translations:
            instance.trans.set(translations)

        return instance

    def update(self, instance, validated_data):
        trans_data = validated_data.pop("trans", None)

        instance = super().update(instance, validated_data)

        if trans_data is not None:
            translations = []
            for data in trans_data:
                trans, updated = Translation.objects.update_or_create(
                    user=instance.user,
                    lang=data["lang"],
                    slug=slugify(data["text"]),
                    defaults={
                        "text": data["text"],
                        "priority": data["priority"],
                    },
                )
                translations.append(trans)

            # @TODO - it may be orphans words/trans... cleanup with cron command?
            if translations:
                instance.trans.set(translations)
            else:
                instance.trans.clear()

        return instance


class LessonSerializer(ModelSerializer):
    translations = TranslationSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "name",
            "created_at",
            "modified_at",
            "priority",
            "is_active",
            "translations",
        ]
        extra_kwargs = {
            "priority": {
                "default": 0,
            },
        }


class LessonSaveSerializer(LessonSerializer):
    translations = PrimaryKeyOwnerRelatedField(
        many=True, required=True, queryset=Translation.objects.all()
    )
    user = HiddenField(default=CurrentUserDefault())

    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ["user"]


class TrainingSerializer(ModelSerializer):
    lesson = LessonSerializer(read_only=True)

    class Meta:
        model = Training
        fields = [
            "id",
            "lesson",
            "started_at",
            "finished_at",
            "score",
        ]


class TrainingCreateSerializer(TrainingSerializer):
    lesson = PrimaryKeyOwnerRelatedField(
        required=True,
        queryset=Lesson.objects.all(),
        validators=[IsActiveLessonValidator()],  # For explicit error message
    )
    user = HiddenField(default=CurrentUserDefault())

    class Meta(TrainingSerializer.Meta):
        fields = ["id", "lesson", "user"]


class TrainingUpdateSerializer(TrainingSerializer):
    class Meta(TrainingSerializer.Meta):
        fields = ["id", "finished_at"]

    def update(self, instance, validated_data):
        instance.score = instance.stats.filter(succeed=True).count()
        return super().update(instance, validated_data)


class StatSerializer(ModelSerializer):
    training = TrainingSerializer()
    translation = TranslationSerializer()

    class Meta:
        model = Stat
        fields = ["id", "created_at", "training", "translation", "succeed"]


class StatSaveSerializer(StatSerializer):
    training = PrimaryKeyOwnerRelatedField(
        required=True, queryset=Training.objects.all()
    )
    translation = PrimaryKeyOwnerRelatedField(
        required=True, queryset=Translation.objects.all()
    )
