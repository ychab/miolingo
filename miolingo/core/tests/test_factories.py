from django.test import TestCase

from miolingo.core.factories import (
    TranslationFactory,
    TranslationLeafFactory,
    UserFactory,
)


class UserFactoryTestCase(TestCase):
    def test_reset_sequence(self):
        user_1 = UserFactory()
        user_1_seq = int(user_1.username.split("_")[-1])

        UserFactory.reset_sequence(force=True)

        user_2 = UserFactory()
        user_2_seq = int(user_2.username.split("_")[-1])

        self.assertEqual(user_2_seq, user_1_seq + 1)


class TranslationFactoryTestCase(TestCase):
    def test_trans_extracted(self):
        trans = [
            TranslationLeafFactory(lang="es"),
        ]
        translation = TranslationFactory(lang="fr", trans=trans)

        self.assertEqual(translation.trans.all().count(), 1)
        self.assertEqual(translation.trans.first().pk, trans[0].pk)
