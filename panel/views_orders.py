from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import Order
from panel.views import staff_required

ORDERS_PER_PAGE = 30


@login_required(login_url='panel:login')
@staff_required
def pedidos_list(request):
    pedidos = Order.objects.all()
    status = request.GET.get('status')
    if status:
        pedidos = pedidos.filter(status=status)
    return render(
        request,
        'panel/pedidos_list.html',
        {
            'active': 'pedidos',
            'pedidos': pedidos[:ORDERS_PER_PAGE],
            'status_atual': status,
            'status_choices': Order.STATUS_CHOICES,
        },
    )


@login_required(login_url='panel:login')
@staff_required
def pedido_detalhe(request, pk):
    pedido = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
    return render(
        request,
        'panel/pedido_detalhe.html',
        {'active': 'pedidos', 'pedido': pedido, 'status_choices': Order.STATUS_CHOICES},
    )


@login_required(login_url='panel:login')
@staff_required
@require_POST
def pedido_status(request, pk):
    pedido = get_object_or_404(Order, pk=pk)
    novo_status = request.POST.get('status')
    if novo_status in dict(Order.STATUS_CHOICES):
        pedido.status = novo_status
        pedido.save(update_fields=['status'])
        messages.success(request, f'Pedido {pedido.code} marcado como {pedido.get_status_display()}.')
    return redirect('panel:pedido_detalhe', pk=pk)
