from rest_framework import serializers
from core.models import Category, Product, Order, OrderItem
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','slug','icon','order']
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    class Meta:
        model = Product
        fields = ['id','name','slug','description','price','stock','icon','featured','category']
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_name','icon','price','qty']
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['code','customer_name','email','phone','address','city','zip','shipping_option','total','status','created_at','items']
class CheckoutItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)
class CheckoutSerializer(serializers.Serializer):
    customer_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField()
    city = serializers.CharField()
    zip = serializers.CharField()
    shipping_option = serializers.CharField()
    items = serializers.ListField(child=CheckoutItemSerializer())
