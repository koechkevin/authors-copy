import django_filters
from .models import ArticlesModel


class ArticlesFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    tag = django_filters.CharFilter(field_name='tags__tag', lookup_expr='exact')
    author = django_filters.CharFilter(field_name='author__username', lookup_expr='icontains')

    class Meta:
        model = ArticlesModel
        fields = ('title', 'description', 'tag', 'author')
