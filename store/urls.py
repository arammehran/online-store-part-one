from django.urls import path, include
from rest_framework import routers

from . import views

# URLConf
urlpatterns = [
    path('products/', views.product_list),
    path('products/<int:id>/', views.product_detail),
    path('collections/', views.collection_list),
    path('customers', include([
        path('', views.CustomerViewSet.as_view()),
    ])
         ),
    path('collections/<int:pk>/', views.collection_detail, name='collection-detail'),
]
