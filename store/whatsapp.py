"""Monta a mensagem de confirmacao do pedido no WhatsApp.

O texto e gerado a partir do pedido ja gravado no banco — o WhatsApp confirma
a compra, nunca a cria. Se o cliente fechar a aba, o pedido continua existindo.
"""

import os
import re
from urllib.parse import quote

from store.checkout_service import shipping_price

WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '5521995095642')
WHATSAPP_BASE = 'https://wa.me/'
SHIPPING_LABEL = {
    'padrao': 'Padrao (5 a 8 dias)',
    'expresso': 'Expresso (1 a 3 dias)',
    'gratis': 'Retirada na loja',
}


def order_message(order):
    linhas = [f'*PEDIDO {order.code}*', order.customer_name, '']
    for item in order.items.all():
        codigo = f' · cod. {item.sku}' if item.sku else ''
        linhas.append(f'{item.qty}x {item.product_name}{codigo}')
        linhas.append(f'    R$ {item.subtotal:.2f}')

    frete = SHIPPING_LABEL.get(order.shipping_option, order.shipping_option)
    linhas += [
        '',
        f'Frete: {frete} — R$ {shipping_price(order.shipping_option):.2f}',
        f'*TOTAL: R$ {order.total:.2f}*',
        '',
        f'Entrega: {order.address}',
        f'{order.city} — CEP {order.zip}',
    ]
    if order.phone:
        linhas.append(f'Contato: {order.phone}')
    return '\n'.join(linhas)


PHONE_RE = re.compile(r'^\d{10,15}$')


def _valid_number(number):
    if not number:
        return WHATSAPP_NUMBER
    digits = re.sub(r'\D', '', number)
    if PHONE_RE.match(digits):
        return digits
    return WHATSAPP_NUMBER


def whatsapp_url(order, number=None):
    return f'{WHATSAPP_BASE}{_valid_number(number)}?text={quote(order_message(order))}'
