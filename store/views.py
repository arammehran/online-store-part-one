from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import status
from .models import Collection, Product
from .serializers import CollectionSerializer, ProductSerializer
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework import views
from store import models as store_models, serializers as store_serializers


class ProductListView(ListCreateAPIView):
    queryset = Product.objects.select_related('collection').all()
    serializer_class = ProductSerializer


class ProductDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        print(product)
        if product.orderitems.count() > 0:
            return Response(
                {'error': 'Product cannot be deleted because it is associated with an order item.'
                 }, 
                 status=status.HTTP_405_METHOD_NOT_ALLOWED
                 )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionListView(ListCreateAPIView):
    queryset = Collection.objects.annotate(products_count=Count('products')).all()
    serializer_class = CollectionSerializer


class CollectionDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.annotate(products_count=Count('products'))
    serializer_class = CollectionSerializer
    # collection = get_object_or_404(
    #     Collection.objects.annotate(
    #         products_count=Count('products')), pk=pk)
    
    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk)
        if collection.products.count() > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerViewSet(views.APIView, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin):
    queryset = store_models.Customer.objects.all()
    serializer_class = store_serializers.CustomerSerializer

    def get(self, request, *args, **kwargs):
        customer = store_models.Customer.objects.get(user_id=request.user.id)
        return Response(self.serializer_class(customer).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        customer = store_models.Customer.objects.get(user_id=request.user.id)
        serializer = self.serializer_class(customer, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
