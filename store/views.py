from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .models import Collection, Product
from .filters import ProductFilter
from .pagination import DefaultPagination
from .serializers import CollectionSerializer, ProductSerializer, ReviewSerializer
from rest_framework.mixins import (
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
    )
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import views, filters
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from store import models as store_models, serializers as store_serializers
from store.permissions import ViewCustomerHistoryPermission, IsAdminOrReadOnly, FullDjangoModelPermissions

class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter,)
    # filterset_fields = ['collection_id']
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'last_update']
    pagination_class = DefaultPagination
    permission_classes = [IsAdminOrReadOnly]
        
    def destroy(self, request, *args, **kwargs):
        if store_models.OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)

    # def delete(self, request, pk):
    #     product = get_object_or_404(Product, pk=pk)
    #     print(product)
    #     if product.orderitems.count() > 0:
    #         return Response(
    #             {'error': 'Product cannot be deleted because it is associated with an order item.'
    #              }, 
    #              status=status.HTTP_405_METHOD_NOT_ALLOWED
    #              )
    #     product.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count('products')).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection__id=kwargs['pk']).count() > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)
    
    # def delete(self, request, pk):
    #     collection = get_object_or_404(Collection, pk=pk)
    #     if collection.products.count() > 0:
    #         return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    #     collection.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerViewSet(ModelViewSet):
    queryset = store_models.Customer.objects.all()
    serializer_class = store_serializers.CustomerSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response('ok')
 
    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAdminUser | IsAuthenticated])
    def me(self, request):
        customer = store_models.Customer.objects.get(
            user_id=request.user.id)
        if request.method == 'GET':
            serializer = store_serializers.CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = store_serializers.CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        

class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return store_models.Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CartViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  GenericViewSet):
    queryset = store_models.Cart.objects.prefetch_related('items__product').all()
    serializer_class = store_serializers.CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return store_serializers.AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return store_serializers.UpdateCartItemSerializer
        return store_serializers.CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        return store_models.CartItem.objects \
            .filter(cart_id=self.kwargs['cart_pk']) \
            .select_related('product')


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = store_serializers.CreateOrderSerializer(
            data=request.data,
            context={'user_id': self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = store_serializers.OrderSerializer(order)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return store_serializers.CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return store_serializers.UpdateOrderSerializer
        return store_serializers.OrderSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return store_models.Order.objects.all()

        customer_id = store_models.Customer.objects.only(
            'id').get(user__id=user.id)
        return store_models.Order.objects.filter(customer_id=customer_id)