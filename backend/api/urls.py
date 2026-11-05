from django.urls import include, path
from rest_framework import routers

from api.views import (
    CartItemViewSet,
    CartViewSet,
    CategoryViewSet,
    ProductViewSet,
)

router = routers.DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register('products', ProductViewSet, basename='products')

cart_list = CartViewSet.as_view({
    'get': 'list',
    'delete': 'destroy',
})
cart_item_list = CartItemViewSet.as_view({
    'post': 'create',
})
cart_item_detail = CartItemViewSet.as_view({
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path('cart/', cart_list, name='cart'),
    path('cart/items/', cart_item_list, name='cart-items'),
    path(
        'cart/items/<int:product_id>/',
        cart_item_detail,
        name='cart-item-detail',
    ),
    path('', include(router.urls)),
]
