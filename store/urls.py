from django.urls import path, include
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers


from . import views

router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('collections', views.CollectionViewSet)

domains_router = routers.NestedSimpleRouter(router, r'products', lookup='product')
domains_router.register(r'reviews', views.ReviewViewSet, basename='product-reviews')

# URLConf
urlpatterns = [
    path('', include(router.urls)),
    path('', include(domains_router.urls)),
]
