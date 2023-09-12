from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class User(AbstractUser):
    source_lang = models.CharField(
        max_length=2,
        choices=settings.MIOLINGO_LANGUAGES,
        null=True,
        blank=True,
    )


class Translation(models.Model):
    lang = models.CharField(max_length=2, choices=settings.MIOLINGO_LANGUAGES)

    text = models.CharField(max_length=2048)
    slug = models.SlugField(max_length=2048, null=True, editable=False)

    priority = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="translations",
    )

    trans = models.ManyToManyField("self")

    class Meta:
        unique_together = ("lang", "slug", "user")

    def __str__(self):
        return f"{self.text} ({self.lang})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.text)
        return super().save(*args, **kwargs)


class Lesson(models.Model):
    name = models.CharField(max_length=256)

    priority = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lessons")

    translations = models.ManyToManyField(Translation, related_name="lessons")

    def __str__(self):
        return self.name


class Training(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="stats",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trainings",
    )

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)

    score = models.PositiveSmallIntegerField(null=True, editable=False)


class Stat(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    training = models.ForeignKey(
        Training,
        on_delete=models.CASCADE,
        related_name="stats",
    )

    translation = models.ForeignKey(
        Translation,
        on_delete=models.CASCADE,
        related_name="stats",
    )

    succeed = models.BooleanField(default=False)
