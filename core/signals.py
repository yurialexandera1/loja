"""Avisa o cliente por e-mail quando o status do pedido muda.

Sem isto, o unico jeito do cliente saber que o pedido foi pago ou enviado
era abrir a pagina do pedido de novo — ninguem faz isso sem ser avisado.
"""

from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from core.models import Order

STATUS_MESSAGE = {
    'pago': 'Recebemos o pagamento do seu pedido {code}. Já vamos preparar para envio.',
    'enviado': 'Seu pedido {code} foi enviado! Em breve chega até você.',
    'entregue': 'Seu pedido {code} foi entregue. Esperamos que goste — obrigado por comprar na Case See!',
    'cancelado': 'Seu pedido {code} foi cancelado. Qualquer dúvida, fale com a gente no WhatsApp.',
}


@receiver(pre_save, sender=Order)
def _remember_previous_status(sender, instance, **kwargs):
    if instance.pk:
        instance._previous_status = (
            Order.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
        )
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def _notify_status_change(sender, instance, created, **kwargs):
    if created:
        return
    previous = getattr(instance, '_previous_status', None)
    if previous == instance.status:
        return
    notify_order_status_change(instance)


def notify_order_status_change(order):
    template = STATUS_MESSAGE.get(order.status)
    if not template or not order.email:
        return
    send_mail(
        subject=f'Case See — pedido {order.code}',
        message=template.format(code=order.code),
        from_email=None,
        recipient_list=[order.email],
        fail_silently=True,
    )
