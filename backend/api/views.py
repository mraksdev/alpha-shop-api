from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api.filters import ProductFilter
from api.serializers import CategorySerializer, ProductSerializer
from catalog.models import Category, Product


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only viewset for categories."""

    queryset = Category.objects.prefetch_related('subcategories').all()
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)
    lookup_field = 'slug'


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only viewset for products."""

    queryset = Product.objects.select_related(
        'subcategory__category',
    ).all()
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductFilter
    lookup_field = 'slug'
