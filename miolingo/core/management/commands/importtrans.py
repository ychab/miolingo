import csv

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import DatabaseError
from django.utils.text import slugify

from miolingo.core.models import Translation

User = get_user_model()

LANGUAGES = list(dict(settings.MIOLINGO_LANGUAGES).keys())
DIRECTORY = settings.PROJECT_DIR / "core" / "data"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("filename")
        parser.add_argument("src", choices=LANGUAGES)
        parser.add_argument("tgt", choices=LANGUAGES)
        parser.add_argument("username")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])
        filepath = DIRECTORY / options["filename"]

        count = 0
        duplicate = 0

        with open(filepath) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["src", "tgt"], delimiter=";")
            for row in reader:
                txt_src = row["src"].strip()
                txt_tgt = row["tgt"].strip()

                try:
                    # First proceed original source.
                    src, created = Translation.objects.get_or_create(
                        lang=options["src"],
                        slug=slugify(txt_src),
                        user=user,
                        defaults={
                            "text": txt_src,
                        },
                    )
                    count += 1 if created else 0
                    duplicate += 1 if not created else 0

                    # Then proceed translation.
                    trans, created = Translation.objects.get_or_create(
                        lang=options["tgt"],
                        slug=slugify(txt_tgt),
                        user=user,
                        defaults={
                            "text": txt_tgt,
                        },
                    )
                    count += 1 if created else 0
                    duplicate += 1 if not created else 0

                    # No worry, ORM will prevent duplicate:
                    # @see https://docs.djangoproject.com/en/4.2/topics/db/examples/many_to_many/
                    src.trans.add(trans)

                except DatabaseError as exc:
                    self.stdout.write(
                        self.style.ERROR(
                            f"An error occured on line {reader.line_num} with: {exc}."
                        )
                    )

        if duplicate:
            self.stdout.write(self.style.WARNING(f"{duplicate} duplicate(s) detected."))

        self.stdout.write(
            self.style.SUCCESS(f"{count} translations are imported successfully.")
        )
