from django.urls import path, include
from rest_framework import routers

from . import views

# URLConf
urlpatterns = [
    path('products/', views.ProductListView.as_view()),
    path('products/<int:id>/', views.ProductDetailView.as_view()),
    path('collections/', views.collection_list),
    path('customers', include([
        path('', views.CustomerViewSet.as_view()),
    ])
         ),
    path('collections/<int:pk>/', views.collection_detail, name='collection-detail'),
]
