from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import get_language, to_locale

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from miolingo.core.models import Lesson, Stat, Training, Translation

User = get_user_model()
current_locale = to_locale(get_language())


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"test+{o.username}@yannickchabbert.fr")
    password = factory.django.Password("test")
    first_name = factory.Faker("first_name", locale=current_locale)
    last_name = factory.Faker("last_name", locale=current_locale)

    source_lang = fuzzy.FuzzyChoice(settings.MIOLINGO_LANGUAGES, getter=lambda c: c[0])

    @classmethod
    def _setup_next_sequence(cls):
        """
        Ensure that sequence username generated is unique.
        """
        try:
            u = User.objects.filter(username__startswith="user_").order_by("-username")[:1][0]  # fmt: skip
        except IndexError:
            return 1
        else:
            return int(u.username.split("_")[1]) + 1


class TranslationLeafFactory(DjangoModelFactory):
    class Meta:
        model = Translation
        django_get_or_create = ("lang", "slug", "user")

    lang = fuzzy.FuzzyChoice(settings.MIOLINGO_LANGUAGES, getter=lambda c: c[0])
    slug = factory.LazyAttribute(lambda o: slugify(o.text))

    priority = fuzzy.FuzzyInteger(0, 10)

    user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def text(self):
        return factory.Faker._get_faker(self.lang).format("text")


class TranslationFactory(TranslationLeafFactory):
    @factory.post_generation
    def trans(self, created, extracted, **kwargs):
        if created:  # pragma: no branch
            trans = []
            if extracted:
                trans = extracted
            else:
                num = kwargs.pop("num", 0)
                for i in range(0, num):
                    trans.append(TranslationLeafFactory(user=self.user, **kwargs))

            if trans:
                self.trans.set(trans)


class LessonFactory(DjangoModelFactory):
    class Meta:
        model = Lesson

    name = factory.Faker("word", locale=current_locale)
    is_active = True
    priority = fuzzy.FuzzyInteger(0, 10)
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def translations(self, created, extracted, **kwargs):
        if created:  # pragma: no branch
            translations = []

            num = kwargs.pop("num", 3)
            for i in range(0, num):
                translations.append(TranslationFactory(user=self.user, **kwargs))

            # In theory, we should got ALWAYS translations for a lesson!
            self.translations.set(translations)


class TrainingFactory(DjangoModelFactory):
    class Meta:
        model = Training

    lesson = factory.SubFactory(LessonFactory)
    user = factory.SubFactory(UserFactory)

    started_at = fuzzy.FuzzyDateTime(now())
    finished_at = fuzzy.FuzzyDateTime(
        start_dt=now() + timedelta(seconds=60),
        end_dt=now() + timedelta(seconds=180),
    )

    score = fuzzy.FuzzyInteger(0, 20)

    @factory.post_generation
    def stats(self, created, extracted, **kwargs):
        if created and extracted:
            count = kwargs.pop("num", 0)

            for translation in self.lesson.translations.all():
                StatFactory(
                    training=self,
                    translation=translation,
                    succeed=bool(count > 0),
                )
                count -= 1


class StatFactory(DjangoModelFactory):
    class Meta:
        model = Stat

    training = factory.SubFactory(TrainingFactory)
    translation = factory.SubFactory(TranslationFactory)

    succeed = fuzzy.FuzzyChoice([True, False])
