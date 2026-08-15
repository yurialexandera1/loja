"""Envio automatico de confirmacao via WhatsApp Cloud API (Meta), oficial.

Sem WHATSAPP_CLOUD_API_TOKEN e WHATSAPP_CLOUD_PHONE_ID no .env, esta funcao
nao faz nada — a loja continua funcionando com o link manual em store/whatsapp.py.
Preencha as duas variaveis depois de criar a conta Meta Business + WhatsApp
Business API para automatizar o envio.
"""

import json
import urllib.error
import urllib.request

from django.conf import settings

from store.whatsapp import order_message

GRAPH_API_VERSION = 'v20.0'


def is_configured():
    return bool(settings.WHATSAPP_CLOUD_API_TOKEN and settings.WHATSAPP_CLOUD_PHONE_ID)


def send_order_confirmation(order):
    """Envia a confirmacao automaticamente. Retorna True se enviou, False se
    a API nao esta configurada ou a chamada falhou (nunca levanta excecao —
    a compra ja foi concluida, uma falha de notificacao nao pode derruba-la)."""
    if not is_configured() or not order.phone:
        return False

    url = f'https://graph.facebook.com/{GRAPH_API_VERSION}/{settings.WHATSAPP_CLOUD_PHONE_ID}/messages'
    payload = {
        'messaging_product': 'whatsapp',
        'to': _e164(order.phone),
        'type': 'text',
        'text': {'body': order_message(order)},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {settings.WHATSAPP_CLOUD_API_TOKEN}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=10):
            return True
    except (urllib.error.URLError, urllib.error.HTTPError):
        return False


def _e164(phone):
    digits = ''.join(ch for ch in phone if ch.isdigit())
    return digits if digits.startswith('55') else f'55{digits}'
