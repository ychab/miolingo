from django.utils.text import slugify
from django.utils.timezone import now

from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.test import APITestCase, override_settings

from miolingo.core.factories import (
    LessonFactory,
    TrainingFactory,
    TranslationFactory,
    UserFactory,
)
from miolingo.core.models import Lesson, Stat, Training, Translation


class UserRetrieveAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("users-me")

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_detail(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["id"], self.user.pk)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["first_name"], self.user.first_name)
        self.assertEqual(response.data["last_name"], self.user.last_name)
        self.assertEqual(response.data["source_lang"], self.user.source_lang)


class UserPartialUpdateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("users-detail", kwargs={"pk": cls.user.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(LANGUAGE_CODE="en")
    def test_username_forbidden(self):
        self.client.force_authenticate(self.user)
        data = {
            "username": "FOO",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.username, "FOO")

    @override_settings(LANGUAGE_CODE="en")
    def test_source_lang_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "source_lang": "foo",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("is not a valid choice.", response.data["source_lang"][0])

    def test_update(self):
        user = UserFactory(
            first_name="foo",
            last_name="foo",
            email="foo@example.com",
            source_lang="en",
        )
        url = reverse("users-detail", kwargs={"pk": user.pk})

        data = {
            "first_name": "bar",
            "last_name": "bar",
            "email": "bar@example.com",
            "source_lang": "fr",
        }
        self.client.force_authenticate(user)
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()

        self.assertEqual(user.first_name, data["first_name"])
        self.assertEqual(user.last_name, data["last_name"])
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.source_lang, data["source_lang"])


class TranslationListAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("translations-list")

    def tearDown(self):
        Translation.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_none(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_owner(self):
        total = 2
        user = UserFactory()
        translations = []
        for i in range(0, 2):
            TranslationFactory(user=user)
            translations.append(TranslationFactory(user=self.user))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": (total * 2) + 1,
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["count"], total)
        self.assertListEqual(
            sorted([w["id"] for w in response.data["results"]]),
            sorted(w.pk for w in translations),
        )

    def test_filter_lang(self):
        translation = TranslationFactory(
            user=self.user,
            lang="fr",
            trans__num=1,
            trans__lang="es",
            trans__text="foo",
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "lang": "fr",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], translation.pk)

    def test_result_ordering_text_asc(self):
        translations = []
        for i in range(0, 3):
            translations.append(TranslationFactory(user=self.user, text=f"{i}"))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": len(translations) + 1,
                "ordering": "text",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            [w["id"] for w in response.data["results"]],
            [w.pk for w in translations],
        )

    def test_result_ordering_text_desc(self):
        translations = []
        for i in range(0, 3):
            translations.append(TranslationFactory(user=self.user, text=f"{i}"))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": len(translations) + 1,
                "ordering": "-text",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            [w["id"] for w in response.data["results"]],
            list(reversed([w.pk for w in translations])),
        )

    def test_result_ordering_priority_asc(self):
        translations = []
        for i in range(0, 3):
            translations.append(TranslationFactory(user=self.user, priority=i))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": len(translations) + 1,
                "ordering": "priority",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            [w["id"] for w in response.data["results"]],
            [w.pk for w in translations],
        )

    def test_result_ordering_priority_desc(self):
        translations = []
        for i in range(0, 3):
            translations.append(TranslationFactory(user=self.user, priority=i))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": len(translations) + 1,
                "ordering": "-priority",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            [w["id"] for w in response.data["results"]],
            list(reversed([w.pk for w in translations])),
        )

    def test_result_pagination(self):
        total = 6
        page_size = 5
        translations = []
        for i in range(0, total):
            translations.append(TranslationFactory(user=self.user, text=f"{i}"))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": page_size,
                "ordering": "text",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["count"], total)
        self.assertEqual(len(response.data["results"]), page_size)
        self.assertTrue(response.data["next"])

        self.assertListEqual(
            sorted([w["id"] for w in response.data["results"]]),
            sorted(w.pk for w in translations)[:page_size],
        )

    def test_result_data(self):
        translation = TranslationFactory(
            user=self.user,
            lang="fr",
            trans__num=1,
            trans__lang="es",
            trans__text="foo",
        )
        trans = translation.trans.first()

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "lang": "fr",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

        self.assertEqual(response.data["results"][0]["lang"], translation.lang)
        self.assertEqual(response.data["results"][0]["text"], translation.text)
        self.assertEqual(response.data["results"][0]["slug"], translation.slug)
        self.assertEqual(response.data["results"][0]["priority"], translation.priority)

        self.assertEqual(len(response.data["results"][0]["trans"]), 1)
        self.assertEqual(response.data["results"][0]["trans"][0]["lang"], trans.lang)
        self.assertEqual(response.data["results"][0]["trans"][0]["text"], trans.text)
        self.assertEqual(response.data["results"][0]["trans"][0]["slug"], trans.slug)
        self.assertEqual(
            response.data["results"][0]["trans"][0]["priority"], trans.priority
        )


class TranslationCreateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("translations-list")

    def tearDown(self):
        Translation.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(LANGUAGE_CODE="en")
    def test_lang_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "lang": "FOO",
            "text": "foo",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("is not a valid choice", response.data["lang"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_priority_invalid(self):
        self.client.force_authenticate(self.user)
        data = {"lang": "fr", "text": "foo", "priority": "FOO"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("A valid integer is required.", response.data["priority"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_unique_together(self):
        translation = TranslationFactory(user=self.user, lang="fr", text="foo")

        self.client.force_authenticate(self.user)
        data = {
            "lang": translation.lang,
            "text": translation.text,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "This translation already exists.",
            response.data[api_settings.NON_FIELD_ERRORS_KEY][0],
        )

    def test_create_without_trans(self):
        self.client.force_authenticate(self.user)
        data = {
            "lang": "fr",
            "text": "foo",
            "priority": 1,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 201)

        obj = Translation.objects.latest("pk")
        self.assertEqual(obj.user, self.user)
        self.assertEqual(obj.lang, data["lang"])
        self.assertEqual(obj.text, data["text"])
        self.assertEqual(obj.priority, data["priority"])
        self.assertEqual(obj.slug, slugify(data["text"]))
        self.assertEqual(obj.trans.all().count(), 0)

    def test_create_with_trans(self):
        self.client.force_authenticate(self.user)
        data = {
            "lang": "fr",
            "text": "foo",
            "trans": [
                {
                    "lang": "es",
                    "text": "barI zou",
                    "priority": 2,
                },
                {
                    "lang": "es",
                    "text": "baz",
                },
            ],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 201)

        obj = Translation.objects.get(user=self.user, lang="fr", slug="foo")
        self.assertEqual(obj.trans.all().count(), 2)

        slug = slugify(data["trans"][0]["text"])
        trans = obj.trans.get(
            user=self.user,
            lang="es",
            slug=slug,
        )
        self.assertEqual(trans.lang, data["trans"][0]["lang"])
        self.assertEqual(trans.text, data["trans"][0]["text"])
        self.assertEqual(trans.priority, data["trans"][0]["priority"])
        self.assertEqual(trans.slug, slug)
        self.assertEqual(trans.user, self.user)

    def test_create_with_trans_exist(self):
        self.client.force_authenticate(self.user)

        trans = TranslationFactory(
            user=self.user,
            lang="es",
            text="foo",
            priority=1,
        )

        data = {
            "lang": "fr",
            "text": "foo",
            "trans": [
                {
                    "lang": trans.lang,
                    "text": trans.text,
                    "priority": 2,
                },
            ],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Translation.objects.all().count(), 2)

        obj = Translation.objects.get(user=self.user, lang="fr", slug="foo")
        self.assertEqual(obj.trans.all().count(), 1)

        self.assertEqual(trans.lang, data["trans"][0]["lang"])
        self.assertEqual(trans.text, data["trans"][0]["text"])
        self.assertEqual(trans.slug, slugify(data["trans"][0]["text"]))
        self.assertNotEqual(trans.priority, data["trans"][0]["priority"])


class TranslationRetrieveAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.obj = TranslationFactory(user=cls.user, trans__num=1)
        cls.url = reverse("translations-detail", kwargs={"pk": cls.obj.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        trans = self.obj.trans.first()

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["lang"], self.obj.lang)
        self.assertEqual(response.data["text"], self.obj.text)
        self.assertEqual(response.data["slug"], self.obj.slug)
        self.assertEqual(response.data["priority"], self.obj.priority)

        self.assertEqual(len(response.data["trans"]), 1)
        self.assertEqual(response.data["trans"][0]["lang"], trans.lang)
        self.assertEqual(response.data["trans"][0]["text"], trans.text)
        self.assertEqual(response.data["trans"][0]["slug"], trans.slug)
        self.assertEqual(response.data["trans"][0]["priority"], trans.priority)


class TranslationPartialUpdateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.obj = TranslationFactory(
            user=cls.user,
            lang="fr",
            text="test",
            trans__num=1,
            trans__lang="es",
            trans__text="test_trad",
        )
        cls.url = reverse("translations-detail", kwargs={"pk": cls.obj.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(LANGUAGE_CODE="en")
    def test_lang_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "lang": "FOO",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("is not a valid choice", response.data["lang"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_priority_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "priority": "FOO",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("A valid integer is required.", response.data["priority"][0])

    def test_update(self):
        self.client.force_authenticate(self.user)

        obj = TranslationFactory(
            user=self.user,
            lang="fr",
            text="foo",
            priority=1,
        )
        url = reverse("translations-detail", kwargs={"pk": obj.pk})

        data = {
            "lang": "es",
            "text": "bar",
            "priority": 2,
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        obj.refresh_from_db()

        self.assertEqual(obj.user, self.user)
        self.assertEqual(obj.lang, data["lang"])
        self.assertEqual(obj.text, data["text"])
        self.assertEqual(obj.priority, data["priority"])

    def test_update_remove_trans(self):
        self.client.force_authenticate(self.user)

        obj = TranslationFactory(
            user=self.user,
            lang="fr",
            text="foo",
            trans__num=1,
            trans__lang="es",
            trans__text="bar",
        )
        url = reverse("translations-detail", kwargs={"pk": obj.pk})

        data = {
            "trans": [],
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)

        obj.refresh_from_db()
        self.assertEqual(obj.trans.all().count(), 0)

    def test_update_replace_trans(self):
        self.client.force_authenticate(self.user)

        obj = TranslationFactory(
            user=self.user,
            lang="fr",
            text="foo",
            trans__num=1,
            trans__lang="es",
            trans__text="bar",
            trans__priority=1,
        )
        trans = obj.trans.first()
        url = reverse("translations-detail", kwargs={"pk": obj.pk})

        data = {
            "trans": [
                {
                    "lang": "es",
                    "text": "baz",
                    "priority": 2,
                },
            ],
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        obj.refresh_from_db()

        new_trans = obj.trans.first()
        self.assertEqual(obj.trans.all().count(), 1)
        self.assertNotEqual(new_trans.pk, trans.pk)
        self.assertEqual(new_trans.lang, data["trans"][0]["lang"])
        self.assertEqual(new_trans.text, data["trans"][0]["text"])
        self.assertEqual(new_trans.priority, data["trans"][0]["priority"])


class TranslationDeleteAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.obj = TranslationFactory(user=cls.user)
        cls.url = reverse("translations-detail", kwargs={"pk": cls.obj.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        obj = TranslationFactory(user=self.user)
        url = reverse("translations-detail", kwargs={"pk": obj.pk})

        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        with self.assertRaises(Translation.DoesNotExist):
            obj.refresh_from_db()


class LessonListAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("lessons-list")

    def tearDown(self):
        Lesson.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_none(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_owner(self):
        total = 2
        user = UserFactory()
        lessons = []
        for i in range(0, 2):
            LessonFactory(user=user)
            lessons.append(LessonFactory(user=self.user))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": (total * 2) + 1,
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["count"], total)
        self.assertListEqual(
            sorted([o["id"] for o in response.data["results"]]),
            sorted(o.pk for o in lessons),
        )

    def test_filter_is_active(self):
        lesson = LessonFactory(
            user=self.user,
            is_active=True,
        )
        LessonFactory(
            user=self.user,
            is_active=False,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "is_active": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], lesson.pk)

    def test_result_ordering_name_asc(self):
        lessons = []
        for i in range(0, 3):
            lessons.append(LessonFactory(user=self.user, name=f"{i}"))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": len(lessons) + 1,
                "ordering": "name",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            [o["id"] for o in response.data["results"]],
            [o.pk for o in lessons],
        )

    def test_result_ordering_name_desc(self):
        lessons = []
        for i in range(0, 3):
            lessons.append(LessonFactory(user=self.user, name=f"{i}"))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": len(lessons) + 1,
                "ordering": "-name",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            [o["id"] for o in response.data["results"]],
            list(reversed([o.pk for o in lessons])),
        )

    def test_result_ordering_priority_asc(self):
        lessons = []
        for i in range(0, 3):
            lessons.append(LessonFactory(user=self.user, priority=i))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": len(lessons) + 1,
                "ordering": "priority",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            [o["id"] for o in response.data["results"]],
            [o.pk for o in lessons],
        )

    def test_result_ordering_priority_desc(self):
        lessons = []
        for i in range(0, 3):
            lessons.append(LessonFactory(user=self.user, priority=i))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": len(lessons) + 1,
                "ordering": "-priority",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            [o["id"] for o in response.data["results"]],
            list(reversed([o.pk for o in lessons])),
        )

    def test_result_pagination(self):
        total = 6
        page_size = 5
        lessons = []
        for i in range(0, total):
            lessons.append(LessonFactory(user=self.user, name=f"{i}"))

        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.url,
            data={
                "page_size": page_size,
                "ordering": "name",
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["count"], total)
        self.assertEqual(len(response.data["results"]), page_size)
        self.assertTrue(response.data["next"])

        self.assertListEqual(
            sorted([o["id"] for o in response.data["results"]]),
            sorted(o.pk for o in lessons)[:page_size],
        )

    @override_settings(TIME_ZONE="UTC")
    def test_result_data(self):
        lesson = LessonFactory(
            user=self.user,
            translations__num=1,
        )
        translation = lesson.translations.first()

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

        self.assertEqual(response.data["results"][0]["name"], lesson.name)
        self.assertEqual(
            response.data["results"][0]["created_at"],
            lesson.created_at.isoformat().replace("+00:00", "Z"),
        )  # noqa
        self.assertEqual(
            response.data["results"][0]["modified_at"],
            lesson.modified_at.isoformat().replace("+00:00", "Z"),
        )  # noqa
        self.assertEqual(response.data["results"][0]["is_active"], lesson.is_active)
        self.assertEqual(response.data["results"][0]["priority"], lesson.priority)

        self.assertEqual(len(response.data["results"][0]["translations"]), 1)
        self.assertEqual(
            response.data["results"][0]["translations"][0]["lang"], translation.lang
        )
        self.assertEqual(
            response.data["results"][0]["translations"][0]["text"], translation.text
        )
        self.assertEqual(
            response.data["results"][0]["translations"][0]["slug"], translation.slug
        )
        self.assertEqual(
            response.data["results"][0]["translations"][0]["priority"],
            translation.priority,
        )


class LessonCreateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("lessons-list")

    def tearDown(self):
        Lesson.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(LANGUAGE_CODE="en")
    def test_is_active_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "name": "foo",
            "priority": 0,
            "is_active": "foo",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Must be a valid boolean.", response.data["is_active"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_priority_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "name": "test",
            "priority": "foo",
            "is_active": True,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("A valid integer is required.", response.data["priority"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_translations_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "name": "test",
            "priority": 1,
            "is_active": True,
            "translations": ["foo"],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Incorrect type. Expected pk value", response.data["translations"][0]
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_translations_not_exists(self):
        self.client.force_authenticate(self.user)
        data = {
            "name": "test",
            "priority": 1,
            "is_active": True,
            "translations": [-3],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("object does not exist", response.data["translations"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_translations_not_owner(self):
        translation = TranslationFactory(user=UserFactory())

        self.client.force_authenticate(self.user)
        data = {
            "name": "test",
            "priority": 1,
            "is_active": True,
            "translations": [translation.pk],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("object does not exist", response.data["translations"][0])

    def test_create(self):
        translations = [TranslationFactory(user=self.user) for _ in range(0, 3)]

        data = {
            "name": "test",
            "priority": 0,
            "is_active": True,
            "translations": [w.pk for w in translations],
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 201)

        obj = Lesson.objects.get(name=data["name"])
        self.assertEqual(obj.translations.all().count(), len(translations))

        self.assertEqual(response.data["name"], obj.name)
        self.assertEqual(response.data["priority"], obj.priority)
        self.assertEqual(response.data["is_active"], obj.is_active)
        self.assertTrue(response.data["created_at"])
        self.assertTrue(response.data["modified_at"])
        self.assertEqual(self.user, obj.user)

        self.assertListEqual(
            sorted([w.pk for w in obj.translations.all()]),
            sorted([w.pk for w in translations]),
        )


class LessonRetrieveAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.obj = LessonFactory(
            user=cls.user, translations__num=1, translations__trans__num=1
        )
        cls.url = reverse("lessons-detail", kwargs={"pk": cls.obj.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    @override_settings(TIME_ZONE="UTC")
    def test_detail(self):
        translation = self.obj.translations.first()
        trans = translation.trans.first()

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["name"], self.obj.name)
        self.assertEqual(
            response.data["created_at"],
            self.obj.created_at.isoformat().replace("+00:00", "Z"),
        )
        self.assertEqual(
            response.data["modified_at"],
            self.obj.modified_at.isoformat().replace("+00:00", "Z"),
        )
        self.assertEqual(response.data["is_active"], self.obj.is_active)
        self.assertEqual(response.data["priority"], self.obj.priority)

        self.assertEqual(len(response.data["translations"]), 1)
        self.assertEqual(response.data["translations"][0]["lang"], translation.lang)
        self.assertEqual(response.data["translations"][0]["text"], translation.text)
        self.assertEqual(response.data["translations"][0]["slug"], translation.slug)
        self.assertEqual(
            response.data["translations"][0]["priority"], translation.priority
        )

        self.assertEqual(len(response.data["translations"][0]["trans"]), 1)
        self.assertEqual(
            response.data["translations"][0]["trans"][0]["lang"], trans.lang
        )
        self.assertEqual(
            response.data["translations"][0]["trans"][0]["text"], trans.text
        )
        self.assertEqual(
            response.data["translations"][0]["trans"][0]["slug"], trans.slug
        )
        self.assertEqual(
            response.data["translations"][0]["trans"][0]["priority"], trans.priority
        )


class LessonPartialUpdateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.obj = LessonFactory(
            user=cls.user,
            translations__num=1,
        )
        cls.url = reverse("lessons-detail", kwargs={"pk": cls.obj.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(LANGUAGE_CODE="en")
    def test_is_active_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "is_active": "foo",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Must be a valid boolean.", response.data["is_active"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_priority_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "priority": "foo",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("A valid integer is required.", response.data["priority"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_translations_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "translations": ["foo"],
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Incorrect type. Expected pk value", response.data["translations"][0]
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_translations_not_exists(self):
        self.client.force_authenticate(self.user)
        data = {
            "translations": [-3],
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("object does not exist", response.data["translations"][0])

    @override_settings(LANGUAGE_CODE="en")
    def test_translations_not_owner(self):
        translation = TranslationFactory(user=UserFactory())

        self.client.force_authenticate(self.user)
        data = {
            "translations": [translation.pk],
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("object does not exist", response.data["translations"][0])

    def test_update(self):
        self.client.force_authenticate(self.user)

        obj = LessonFactory(
            user=self.user,
            name="foo",
            priority=0,
            is_active=True,
        )
        url = reverse("lessons-detail", kwargs={"pk": obj.pk})

        data = {
            "name": "bar",
            "priority": 1,
            "is_active": False,
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        obj.refresh_from_db()

        self.assertEqual(obj.name, data["name"])
        self.assertEqual(obj.priority, data["priority"])
        self.assertEqual(obj.is_active, data["is_active"])

    def test_update_add_translations(self):
        self.client.force_authenticate(self.user)

        translation = TranslationFactory(user=self.user)
        obj = LessonFactory(
            user=self.user,
            translations__num=1,
        )
        url = reverse("lessons-detail", kwargs={"pk": obj.pk})

        data = {
            "translations": [obj.translations.first().pk, translation.pk],
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        obj.refresh_from_db()

        self.assertEqual(obj.translations.all().count(), 2)
        self.assertIn(translation.pk, [w.pk for w in obj.translations.all()])

    def test_update_remove_translations(self):
        self.client.force_authenticate(self.user)

        obj = LessonFactory(
            user=self.user,
            translations__num=2,
        )
        translation = obj.translations.first()
        url = reverse("lessons-detail", kwargs={"pk": obj.pk})

        data = {
            "translations": [translation.pk],
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        obj.refresh_from_db()

        self.assertEqual(obj.translations.all().count(), 1)
        self.assertIn(translation.pk, [w.pk for w in obj.translations.all()])

    def test_update_replace_translations(self):
        self.client.force_authenticate(self.user)

        obj = LessonFactory(
            user=self.user,
            translations__num=2,
        )
        url = reverse("lessons-detail", kwargs={"pk": obj.pk})

        translations = [TranslationFactory(user=self.user) for _ in range(0, 3)]
        data = {
            "translations": [w.pk for w in translations],
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        obj.refresh_from_db()

        self.assertEqual(obj.translations.all().count(), 3)
        self.assertListEqual(
            sorted([w.pk for w in obj.translations.all()]),
            sorted([w.pk for w in translations]),
        )


class LessonDeleteAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.obj = LessonFactory(user=cls.user)
        cls.url = reverse("lessons-detail", kwargs={"pk": cls.obj.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        obj = LessonFactory(user=self.user)
        url = reverse("lessons-detail", kwargs={"pk": obj.pk})

        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        with self.assertRaises(Lesson.DoesNotExist):
            obj.refresh_from_db()


class TrainingCreateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.lesson = LessonFactory(
            user=cls.user,
            translations__num=1,
            translations__trans__num=1,
        )
        cls.url = reverse("trainings-list")

    def tearDown(self):
        Training.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(LANGUAGE_CODE="en")
    def test_lesson_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "lesson": "FOO",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Incorrect type. Expected pk value, received str.",
            response.data["lesson"][0],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_lesson_not_exists(self):
        self.client.force_authenticate(self.user)
        data = {
            "lesson": 9999999,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f"Invalid pk \"{data['lesson']}\" - object does not exist.",
            response.data["lesson"][0],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_lesson_not_owner(self):
        self.client.force_authenticate(self.user)

        lesson = LessonFactory()
        data = {
            "lesson": lesson.pk,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f"Invalid pk \"{data['lesson']}\" - object does not exist.",
            response.data["lesson"][0],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_lesson_not_active(self):
        self.client.force_authenticate(self.user)

        lesson = LessonFactory(user=self.user, is_active=False)
        data = {
            "lesson": lesson.pk,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("The lesson is inactive.", response.data["lesson"][0])

    def test_create(self):
        data = {
            "lesson": self.lesson.pk,
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 201)

        obj = Training.objects.last()
        self.assertEqual(response.data["lesson"], obj.lesson.pk)
        self.assertEqual(obj.user, self.user)


class TrainingPartialUpdateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.training = TrainingFactory(user=cls.user)
        cls.url = reverse("trainings-detail", kwargs={"pk": cls.training.pk})

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(LANGUAGE_CODE="en")
    def test_finished_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "finished_at": "FOO",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Datetime has wrong format. Use one of these formats instead:",
            response.data["finished_at"][0],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_finished_format_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "finished_at": "06/10/2023 14h12m15s",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Datetime has wrong format. Use one of these formats instead:",
            response.data["finished_at"][0],
        )

    @override_settings(TIME_ZONE="UTC")
    def test_update(self):
        self.client.force_authenticate(self.user)

        lesson = LessonFactory(
            user=self.user,
            translations__num=3,
            translations__trans__num=1,
        )
        training = TrainingFactory(
            lesson=lesson,
            user=self.user,
            stats=True,
            stats__num=2,
        )
        url = reverse("trainings-detail", kwargs={"pk": training.pk})

        data = {
            "finished_at": now().isoformat(),
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        training.refresh_from_db()

        self.assertEqual(response.data["id"], training.pk)
        self.assertEqual(
            response.data["finished_at"],
            training.finished_at.isoformat().replace("+00:00", "Z"),
        )
        self.assertEqual(training.score, 2)


class StatCreateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.lesson = LessonFactory(
            user=cls.user,
            translations__num=3,
            translations__trans__num=1,
        )
        cls.training = TrainingFactory(
            user=cls.user,
            lesson=cls.lesson,
        )
        cls.url = reverse("stats-list")

    def tearDown(self):
        Stat.objects.all().delete()

    def test_access_anonymous(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(LANGUAGE_CODE="en")
    def test_training_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "training": "FOO",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Incorrect type. Expected pk value, received str.",
            response.data["training"][0],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_training_not_exists(self):
        self.client.force_authenticate(self.user)
        data = {
            "training": 9999999,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f"Invalid pk \"{data['training']}\" - object does not exist.",
            response.data["training"][0],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_training_not_owner(self):
        self.client.force_authenticate(self.user)

        training = TrainingFactory()
        data = {
            "training": training.pk,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f"Invalid pk \"{data['training']}\" - object does not exist.",
            response.data["training"][0],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_translation_invalid(self):
        self.client.force_authenticate(self.user)
        data = {
            "translation": "FOO",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Incorrect type. Expected pk value, received str.",
            response.data["translation"][0],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_translation_not_exists(self):
        self.client.force_authenticate(self.user)
        data = {
            "translation": 9999999,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f"Invalid pk \"{data['translation']}\" - object does not exist.",
            response.data["translation"][0],
        )  # noqa

    @override_settings(LANGUAGE_CODE="en")
    def test_translation_not_owner(self):
        self.client.force_authenticate(self.user)

        translation = TranslationFactory()
        data = {
            "translation": translation.pk,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f"Invalid pk \"{data['translation']}\" - object does not exist.",
            response.data["translation"][0],
        )  # noqa

    def test_create(self):
        translation = self.training.lesson.translations.first()

        data = {
            "training": self.training.pk,
            "translation": translation.pk,
            "succeed": True,
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 201)

        obj = Stat.objects.last()
        self.assertEqual(response.data["training"], obj.training.pk)
        self.assertEqual(response.data["translation"], translation.pk)
        self.assertEqual(response.data["succeed"], obj.succeed)
