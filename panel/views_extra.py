from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import ProductReview, ReferralCode
from panel.views import staff_required

PANEL_LIST_PER_PAGE = 25


@login_required(login_url='panel:login')
@staff_required
def avaliacoes_list(request):
    avaliacoes = ProductReview.objects.select_related('product').all()
    apenas_pendentes = request.GET.get('pendentes') == '1'
    if apenas_pendentes:
        avaliacoes = avaliacoes.filter(approved=False)
    paginator = Paginator(avaliacoes, PANEL_LIST_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'panel/avaliacoes_list.html',
        {
            'active': 'avaliacoes',
            'avaliacoes': page_obj,
            'page_obj': page_obj,
            'apenas_pendentes': apenas_pendentes,
        },
    )


@login_required(login_url='panel:login')
@staff_required
@require_POST
def avaliacao_aprovar(request, pk):
    review = get_object_or_404(ProductReview, pk=pk)
    review.approved = True
    review.save(update_fields=['approved'])
    messages.success(request, 'Avaliação aprovada.')
    return redirect('panel:avaliacoes')


@login_required(login_url='panel:login')
@staff_required
@require_POST
def avaliacao_remover(request, pk):
    ProductReview.objects.filter(pk=pk).delete()
    messages.success(request, 'Avaliação removida.')
    return redirect('panel:avaliacoes')


@login_required(login_url='panel:login')
@staff_required
def indicacoes_list(request):
    paginator = Paginator(ReferralCode.objects.all(), PANEL_LIST_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'panel/indicacoes_list.html',
        {'active': 'indicacoes', 'indicacoes': page_obj, 'page_obj': page_obj},
    )
