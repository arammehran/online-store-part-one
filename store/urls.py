from django.urls import path, include
from rest_framework import routers

from . import views

# URLConf
urlpatterns = [
    path('products/', views.ProductListView.as_view()),
    path('products/<int:pk>/', views.ProductDetailView.as_view()),
    path('collections/', views.CollectionListView.as_view()),
    path('customers', include([
        path('', views.CustomerViewSet.as_view()),
    ])
         ),
    path('collections/<int:pk>/', views.CollectionDetailView.as_view(), name='collection-detail'),
]
