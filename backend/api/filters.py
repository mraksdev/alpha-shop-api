from django_filters import rest_framework as filters

from catalog.models import Product


class ProductFilter(filters.FilterSet):
    """Filter products by category and subcategory slugs."""

    category = filters.CharFilter(
        field_name='subcategory__category__slug',
    )
    subcategory = filters.CharFilter(
        field_name='subcategory__slug',
    )

    class Meta:
        model = Product
        fields = ('category', 'subcategory')
