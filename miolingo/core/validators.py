from django.utils.text import gettext_lazy as _
from django.utils.text import slugify

from rest_framework.exceptions import ValidationError

from miolingo.core.models import Translation


class UniqueTogetherTranslationValidator:
    requires_context = True

    def __call__(self, attrs, serializer):
        qs = Translation.objects.all()
        lang = attrs.get("lang", None)
        text = attrs.get("text", None)

        if serializer.instance:
            qs = qs.exclude(pk=serializer.instance.pk)
            lang = lang or serializer.instance.lang
            text = text or serializer.instance.text

        filters = {
            "user": serializer.context["request"].user,
            "lang": lang,
            "slug": slugify(text),
        }

        exists = qs.filter(**filters).exists()
        if exists:
            raise ValidationError(
                detail=_("This translation already exists."),
                code="unique",
            )


class IsActiveLessonValidator:
    def __call__(self, lesson):
        if not lesson.is_active:
            raise ValidationError(_("The lesson is inactive."))
