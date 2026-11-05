from django.urls import include, path
from rest_framework import routers

from api.views import CategoryViewSet, ProductViewSet

router = routers.DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register('products', ProductViewSet, basename='products')

urlpatterns = [
    path('', include(router.urls)),
]
