from io import StringIO
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from miolingo.core.factories import UserFactory
from miolingo.core.models import Translation

User = get_user_model()


@mock.patch(
    "miolingo.core.management.commands.importtrans.DIRECTORY",
    new=settings.PROJECT_DIR / "core" / "tests" / "data",
)
class ImportTransCommandTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def tearDown(self):
        Translation.objects.all().delete()

    def test_import_succeed(self):
        out = StringIO()
        args = [
            "test_succeed-fr_es.csv",
            "fr",
            "es",
            self.user.username,
        ]
        call_command("importtrans", stdout=out, *args)
        self.assertIn("40 translations are imported successfully.", out.getvalue())

    def test_import_duplicate(self):
        out = StringIO()
        args = [
            "test_duplicate-fr_es.csv",
            "fr",
            "es",
            self.user.username,
        ]
        call_command("importtrans", stdout=out, *args)
        self.assertIn("2 duplicate(s) detected.", out.getvalue())

    def test_import_error(self):
        out = StringIO()
        args = [
            "test_error-fr_es.csv",
            "fr",
            "es",
            self.user.username,
        ]
        call_command("importtrans", stdout=out, *args)
        self.assertIn("An error occured on line 1 with:", out.getvalue())
