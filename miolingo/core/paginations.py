from django.conf import settings

from rest_framework.pagination import PageNumberPagination


class MiolingoPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = settings.MIOLINGO_PAGINATION_MAX_PAGE_SIZE
