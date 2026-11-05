from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import ProductFilter
from api.serializers import (
    CartItemAddSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
    CategorySerializer,
    ProductSerializer,
)
from cart.models import Cart, CartItem
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


class UserCartMixin:
    """Mixin for getting the cart of the current user."""

    def get_cart(self):
        """Return the current user's cart, creating it if needed."""
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartViewSet(UserCartMixin, viewsets.GenericViewSet):
    """Viewset for viewing and clearing the current user's cart."""

    permission_classes = (IsAuthenticated,)
    serializer_class = CartSerializer

    def list(self, request):
        """Return the current user's cart with totals."""
        cart = self.get_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    def destroy(self, request):
        """Remove all products from the current user's cart."""
        cart = self.get_cart()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemViewSet(UserCartMixin, viewsets.GenericViewSet):
    """Viewset for adding, changing and removing cart items."""

    permission_classes = (IsAuthenticated,)
    serializer_class = CartItemSerializer
    lookup_field = 'product_id'
    lookup_url_kwarg = 'product_id'

    def get_queryset(self):
        """Return only items from the current user's cart."""
        return CartItem.objects.filter(
            cart__user=self.request.user,
        ).select_related('product__subcategory__category')

    def get_serializer_class(self):
        """Return a serializer depending on the current action."""
        if self.action == 'create':
            return CartItemAddSerializer
        if self.action == 'partial_update':
            return CartItemUpdateSerializer
        return CartItemSerializer

    def create(self, request):
        """Add a product to the cart or increase its quantity."""
        context = self.get_serializer_context()
        context['cart'] = self.get_cart()
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        output = CartItemSerializer(
            item,
            context=self.get_serializer_context(),
        )
        status_code = (
            status.HTTP_201_CREATED
            if serializer.created
            else status.HTTP_200_OK
        )
        return Response(output.data, status=status_code)

    def partial_update(self, request, product_id=None):
        """Change the quantity of a product in the cart."""
        item = self.get_object()
        serializer = self.get_serializer(
            item,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output = CartItemSerializer(
            item,
            context=self.get_serializer_context(),
        )
        return Response(output.data)

    def destroy(self, request, product_id=None):
        """Remove a product from the cart."""
        item = self.get_object()
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
