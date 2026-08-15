from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from core.models import (
    BlogPost,
    Brand,
    Category,
    Coupon,
    Order,
    OrderItem,
    Product,
    ProductImage,
    ProductReview,
    ReferralCode,
    ShippingZone,
    SiteSettings,
    Variant,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'order', 'product_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    fields = ['name', 'slug', 'icon', 'order', 'seo_text']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_product_count=Count('products'))

    @admin.display(description='produtos', ordering='_product_count')
    def product_count(self, category):
        return category._product_count


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt', 'order']


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ['color', 'size', 'sku', 'stock']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'sku',
        'brand',
        'category',
        'price',
        'stock_label',
        'is_inclusive',
        'active',
    ]
    list_filter = ['category', 'brand', 'is_inclusive', 'active', 'featured']
    list_editable = ['price', 'active']
    search_fields = ['name', 'sku', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['sold_count', 'created_at']
    inlines = [ProductImageInline, VariantInline]
    list_select_related = ['brand', 'category']
    fieldsets = [
        ('Identificacao', {'fields': ['name', 'slug', 'sku', 'brand', 'category']}),
        ('Venda', {'fields': ['price', 'compare_at_price', 'stock', 'sold_count']}),
        (
            'Vitrine',
            {'fields': ['description', 'icon', 'is_inclusive', 'featured', 'active']},
        ),
        ('Registro', {'fields': ['created_at'], 'classes': ['collapse']}),
    ]

    @admin.display(description='estoque', ordering='stock')
    def stock_label(self, product):
        if not product.in_stock:
            return format_html('<b style="color:#a32b22">esgotado</b>')
        if product.is_low_stock:
            return format_html('<b style="color:#a66412">{} restantes</b>', product.stock)
        return product.stock


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'sku', 'price', 'qty', 'subtotal_label']
    can_delete = False

    @admin.display(description='subtotal')
    def subtotal_label(self, item):
        return f'R$ {item.subtotal:.2f}'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['code', 'customer_name', 'city', 'total', 'status', 'created_at']
    list_filter = ['status', 'shipping_option', 'created_at']
    search_fields = ['code', 'customer_name', 'email', 'phone']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    readonly_fields = ['code', 'total', 'created_at', 'whatsapp_sent_at']
    actions = ['marcar_pago', 'marcar_enviado']

    @admin.action(description='Marcar como pago')
    def marcar_pago(self, request, queryset):
        atualizados = queryset.update(status='pago')
        self.message_user(request, f'{atualizados} pedido(s) marcados como pagos.')

    @admin.action(description='Marcar como enviado')
    def marcar_enviado(self, request, queryset):
        atualizados = queryset.update(status='enviado')
        self.message_user(request, f'{atualizados} pedido(s) marcados como enviados.')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'percent_off', 'active', 'used_count', 'max_uses', 'expires_at']
    list_filter = ['active']
    search_fields = ['code']
    readonly_fields = ['used_count', 'created_at']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'author_name', 'rating', 'approved', 'created_at']
    list_filter = ['approved', 'rating']
    list_editable = ['approved']
    search_fields = ['product__name', 'author_name', 'comment']
    actions = ['aprovar']

    @admin.action(description='Aprovar avaliacoes selecionadas')
    def aprovar(self, request, queryset):
        atualizadas = queryset.update(approved=True)
        self.message_user(request, f'{atualizadas} avaliacao(oes) aprovadas.')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'published', 'created_at']
    list_filter = ['published']
    list_editable = ['published']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'owner_name', 'owner_email', 'uses', 'reward_threshold', 'reward_unlocked']
    search_fields = ['code', 'owner_name', 'owner_email']
    readonly_fields = ['code', 'uses', 'created_at']

    @admin.display(boolean=True, description='recompensa liberada')
    def reward_unlocked(self, referral):
        return referral.reward_unlocked


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'cep_start', 'cep_end', 'price', 'days_min', 'days_max', 'active']
    list_filter = ['active']
    list_editable = ['active']
    search_fields = ['name', 'cep_start', 'cep_end']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'updated_at']
    readonly_fields = ['updated_at']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
