from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from miolingo.core.models import Lesson, Stat, Training, Translation


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "lang",
        "priority",
        "trans_link",
        "user",
    ]
    list_display_links = ["id"]
    list_select_related = ["user"]
    list_filter = ["lang"]
    ordering = ["lang", "text"]
    search_fields = ["text"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("trans")
        qs = qs.select_related("user")  # Just in case list_select_related fail
        return qs

    def trans_link(self, obj):
        if obj.trans.all().count() > 0:
            output = "<ul>"
            for translation in obj.trans.all():
                url = reverse("admin:core_translation_change", args=(translation.pk,))
                output += f'<li><a href="{url}">{translation}</a></li>'
            output += "</ul>"

            return format_html(output)

    trans_link.short_description = "Trans"


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "priority",
        "is_active",
        "modified_at",
        "user",
    ]
    list_display_links = ["name"]
    list_select_related = ["user"]
    list_filter = ["is_active"]
    ordering = ["-modified_at"]
    search_fields = ["name"]


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "lesson_link",
        "started_at",
        "finished_at",
        "score",
        "user",
    ]
    list_display_links = ["id"]
    list_select_related = ["lesson", "user"]
    ordering = ["-finished_at"]
    search_fields = ["lesson__name"]

    def lesson_link(self, obj):
        url = reverse("admin:core_lesson_change", args=(obj.lesson.pk,))
        return format_html(f'<a href="{url}">{obj.lesson}</a>')

    lesson_link.short_description = "Lesson"


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "training_link",
        "translation_link",
        "succeed",
    ]
    list_display_links = ["id"]
    list_select_related = ["training", "translation"]
    list_filter = ["succeed"]
    ordering = ["-created_at"]
    search_fields = ["training__lesson__name", "translation__slug"]

    def training_link(self, obj):
        url = reverse("admin:core_training_change", args=(obj.training.pk,))
        return format_html(f'<a href="{url}">{obj.training}</a>')

    training_link.short_description = "Training"

    def translation_link(self, obj):
        url = reverse("admin:core_translation_change", args=(obj.translation.pk,))
        return format_html(f'<a href="{url}">{obj.translation}</a>')

    translation_link.short_description = "Translation"
