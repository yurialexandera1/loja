from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import CategoryViewSet, ProductViewSet, checkout_api
router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('products', ProductViewSet)

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/', checkout_api),
]
