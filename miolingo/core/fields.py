from rest_framework.relations import PrimaryKeyRelatedField


class PrimaryKeyOwnerRelatedField(PrimaryKeyRelatedField):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(user=self.context["request"].user)
        return qs
