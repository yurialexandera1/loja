import secrets
import string
from decimal import Decimal

from django.db import models, transaction

from core.models import Order, OrderItem, Product, ReferralCode, ShippingZone

REFERRAL_DISCOUNT_PERCENT = 10

SHIPPING_PRICE = {
    'padrao': Decimal('15'),
    'expresso': Decimal('30'),
    'gratis': Decimal('0'),
}
DEFAULT_SHIPPING = 'padrao'
CODE_ALPHABET = string.ascii_uppercase + string.digits
CODE_LENGTH = 8
CODE_PREFIX = 'CS-'


class OutOfStock(Exception):
    """Raised when a line cannot be fulfilled with the stock on hand."""

    def __init__(self, product_name, requested, available):
        self.product_name = product_name
        self.requested = requested
        self.available = available
        super().__init__(f'{product_name}: pedido {requested}, disponivel {available}')


def shipping_price(option, cep=None):
    """Frete pela faixa de CEP quando cadastrada; senao cai na tabela fixa.

    A faixa de CEP e uma aproximacao gratuita (sem contrato com os Correios) —
    mais precisa que a tabela fixa, mas nao consulta nenhum servico externo.
    """
    if cep:
        zone = ShippingZone.objects.for_cep(cep)
        if zone:
            return zone.price
    return SHIPPING_PRICE.get(option, SHIPPING_PRICE[DEFAULT_SHIPPING])


@transaction.atomic
def create_order(request, data, lines, coupon=None, referral=None):
    """Create an order, reserving stock atomically.

    Prices always come from the database, never from the submitted line,
    so a tampered cookie or API payload cannot change what is charged.
    An invalid or expired coupon is silently ignored rather than blocking
    the purchase — the caller already validated it at form time.
    A referral code only applies when there is no coupon, so discounts
    never stack.
    """
    reserved = _reserve_stock(lines)
    goods_subtotal = sum((item['price'] * item['qty'] for item in reserved), Decimal('0'))
    shipping = shipping_price(data.get('shipping_option', DEFAULT_SHIPPING), cep=data.get('zip'))

    applied_coupon = coupon if coupon and coupon.is_valid() else None
    if applied_coupon:
        discount = applied_coupon.discount_for(goods_subtotal)
    elif referral:
        discount = (goods_subtotal * REFERRAL_DISCOUNT_PERCENT / 100).quantize(Decimal('0.01'))
    else:
        discount = Decimal('0')
    total = goods_subtotal - discount + shipping

    order = Order.objects.create(
        code=_generate_code(),
        customer_name=data['customer_name'],
        email=data['email'],
        phone=data.get('phone', ''),
        address=data['address'],
        city=data['city'],
        zip=data['zip'],
        shipping_option=data.get('shipping_option', DEFAULT_SHIPPING),
        coupon=applied_coupon,
        discount=discount,
        total=total,
        status='pendente',
    )
    if applied_coupon:
        applied_coupon.used_count = models.F('used_count') + 1
        applied_coupon.save(update_fields=['used_count'])
    elif referral:
        referral.register_use()
    OrderItem.objects.bulk_create(
        OrderItem(
            order=order,
            product_name=item['name'],
            sku=item['sku'],
            icon=item['icon'],
            price=item['price'],
            qty=item['qty'],
        )
        for item in reserved
    )
    return order


def _reserve_stock(lines):
    """Lock each product row, validate stock, then decrement it."""
    wanted = _merge_lines(lines)
    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(
            id__in=list(wanted.keys()), active=True
        )
    }

    reserved = []
    for product_id, qty in wanted.items():
        product = products.get(product_id)
        if product is None:
            raise OutOfStock(f'produto {product_id}', qty, 0)
        if qty > product.stock:
            raise OutOfStock(product.name, qty, product.stock)
        product.stock -= qty
        product.save(update_fields=['stock'])
        reserved.append(
            {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'icon': product.icon,
                'price': product.price,
                'qty': qty,
            }
        )
    return reserved


def _merge_lines(lines):
    """Collapse duplicate ids so the same product is locked and checked once."""
    merged = {}
    for line in lines:
        product_id = int(line['id'])
        qty = int(line['qty'])
        if qty <= 0:
            continue
        merged[product_id] = merged.get(product_id, 0) + qty
    return merged


def _generate_code():
    while True:
        code = CODE_PREFIX + ''.join(
            secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH)
        )
        if not Order.objects.filter(code=code).exists():
            return code
