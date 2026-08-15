from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from core.models import Category, Product, Order, OrderItem
from api.serializers import CategorySerializer, ProductSerializer, OrderSerializer, CheckoutSerializer
from store.checkout_service import OutOfStock, create_order, SHIPPING_PRICE
from decimal import Decimal
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(active=True)
    serializer_class = ProductSerializer
    def get_queryset(self):
        qs = Product.objects.filter(active=True)
        cat = self.request.query_params.get('categoria')
        busca = self.request.query_params.get('busca')
        if cat:
            qs = qs.filter(category__slug=cat)
        if busca:
            qs = qs.filter(name__icontains=busca)
        return qs
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def checkout_api(request):
    s = CheckoutSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    items = s.validated_data['items']
    product_ids = [i['id'] for i in items]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids, active=True)}
    lines = []
    subtotal = Decimal('0')
    for it in items:
        p = products.get(it['id'])
        if not p:
            return Response({'error': 'Produto invalido'}, status=400)
        qty = it['qty']
        lines.append({'id': p.id,'name': p.name,'price': float(p.price),'qty': qty,'icon': p.icon})
        subtotal += Decimal(str(p.price)) * qty
    try:
        order = create_order(request, s.validated_data, lines)
    except OutOfStock as falta:
        return Response(
            {
                'error': 'estoque_insuficiente',
                'produto': falta.product_name,
                'solicitado': falta.requested,
                'disponivel': falta.available,
            },
            status=status.HTTP_409_CONFLICT,
        )
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
checkout_api.throttle_scope = 'checkout'
