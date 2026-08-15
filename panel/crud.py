"""CRUD generico para as entidades de catalogo do painel.

Um unico par de templates (panel/list.html + panel/form.html) atende
Category, Brand, Coupon, ShippingZone e BlogPost — evita reescrever a
mesma tabela e o mesmo formulario cinco vezes. Nomes de rota sao passados
explicitamente (nao inferidos do slug) para o template nao precisar montar
`{% url %}` dinamico, que o Django nao suporta com filtros encadeados.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render

from panel.views import staff_required

PAGE_SIZE = 25


def crud_views(
    *, model, form_fields, columns, name_singular, name_plural, slug,
    list_url_name, create_url_name, edit_url_name, delete_url_name,
    select_related=None,
):
    """Gera (list_view, create_view, edit_view, delete_view) para um model.

    columns: lista de (atributo, rotulo) exibidos na tabela.
    select_related: tupla opcional de nomes de FK a pre-carregar na listagem,
        evitando N+1 quando columns acessam atributos via relacao.
    """

    if form_fields == '__all__' or not isinstance(form_fields, (list, tuple)):
        raise ValueError(
            f"crud_views({model.__name__}): form_fields deve ser uma lista/tupla "
            "explicita de campos — '__all__' ou valores implicitos nao sao aceitos "
            "(risco de mass assignment)."
        )

    _Form = modelform_factory(model, fields=form_fields)

    @login_required(login_url='panel:login')
    @staff_required
    def list_view(request):
        queryset = model.objects.all()
        if select_related:
            queryset = queryset.select_related(*select_related)

        paginator = Paginator(queryset, PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get('page'))

        rows = [
            {'pk': obj.pk, 'cells': [getattr(obj, attr) for attr, _ in columns]}
            for obj in page_obj.object_list
        ]
        return render(
            request,
            'panel/list.html',
            {
                'active': slug,
                'headers': [label for _, label in columns],
                'rows': rows,
                'page_obj': page_obj,
                'title': name_plural,
                'create_label': f'Novo {name_singular}',
                'create_url_name': create_url_name,
                'edit_url_name': edit_url_name,
                'delete_url_name': delete_url_name,
            },
        )

    @login_required(login_url='panel:login')
    @staff_required
    def create_view(request):
        form = _Form(request.POST or None, request.FILES or None)
        if request.method == 'POST' and form.is_valid():
            form.save()
            messages.success(request, f'{name_singular.capitalize()} criado com sucesso.')
            return redirect(list_url_name)
        return render(
            request,
            'panel/form.html',
            {'active': slug, 'form': form, 'title': f'Novo {name_singular}'},
        )

    @login_required(login_url='panel:login')
    @staff_required
    def edit_view(request, pk):
        instance = get_object_or_404(model, pk=pk)
        form = _Form(request.POST or None, request.FILES or None, instance=instance)
        if request.method == 'POST' and form.is_valid():
            form.save()
            messages.success(request, f'{name_singular.capitalize()} atualizado.')
            return redirect(list_url_name)
        return render(
            request,
            'panel/form.html',
            {'active': slug, 'form': form, 'title': f'Editar {name_singular}', 'instance': instance},
        )

    @login_required(login_url='panel:login')
    @staff_required
    def delete_view(request, pk):
        instance = get_object_or_404(model, pk=pk)
        if request.method == 'POST':
            instance.delete()
            messages.success(request, f'{name_singular.capitalize()} removido.')
            return redirect(list_url_name)
        return render(
            request,
            'panel/confirm_delete.html',
            {
                'active': slug,
                'instance': instance,
                'title': f'Remover {name_singular}',
                'cancel_url_name': list_url_name,
            },
        )

    return list_view, create_view, edit_view, delete_view
