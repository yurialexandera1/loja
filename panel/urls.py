from django.urls import path

from panel import views, views_catalog, views_extra, views_orders, views_products

app_name = 'panel'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('entrar/', views.login_view, name='login'),
    path('sair/', views.logout_view, name='logout'),

    path('pedidos/', views_orders.pedidos_list, name='pedidos'),
    path('pedidos/<str:pk>/', views_orders.pedido_detalhe, name='pedido_detalhe'),
    path('pedidos/<str:pk>/status/', views_orders.pedido_status, name='pedido_status'),

    path('produtos/', views_products.produtos_list, name='produtos'),
    path('produtos/novo/', views_products.produto_novo, name='produto_novo'),
    path('produtos/fotos-em-lote/', views_products.produtos_fotos_lote, name='produtos_fotos_lote'),
    path('produtos/<int:pk>/rapido/', views_products.produto_rapido, name='produto_rapido'),
    path('produtos/<int:pk>/', views_products.produto_editar, name='produto_editar'),
    path('produtos/<int:pk>/remover/', views_products.produto_remover, name='produto_remover'),
    path('produtos/<int:pk>/fotos/', views_products.produto_foto_nova, name='produto_foto_nova'),
    path('produtos/<int:pk>/fotos/<int:image_id>/remover/', views_products.produto_foto_remover, name='produto_foto_remover'),
    path('produtos/<int:pk>/variantes/', views_products.produto_variante_nova, name='produto_variante_nova'),
    path('produtos/<int:pk>/variantes/<int:variant_id>/editar/', views_products.produto_variante_editar, name='produto_variante_editar'),
    path('produtos/<int:pk>/variantes/<int:variant_id>/remover/', views_products.produto_variante_remover, name='produto_variante_remover'),

    path('categorias/', views_catalog.categorias_list, name='categorias'),
    path('categorias/nova/', views_catalog.categoria_nova, name='categoria_nova'),
    path('categorias/<int:pk>/', views_catalog.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/remover/', views_catalog.categoria_remover, name='categoria_remover'),

    path('marcas/', views_catalog.marcas_list, name='marcas'),
    path('marcas/nova/', views_catalog.marca_nova, name='marca_nova'),
    path('marcas/<int:pk>/', views_catalog.marca_editar, name='marca_editar'),
    path('marcas/<int:pk>/remover/', views_catalog.marca_remover, name='marca_remover'),

    path('cupons/', views_catalog.cupons_list, name='cupons'),
    path('cupons/novo/', views_catalog.cupom_novo, name='cupom_novo'),
    path('cupons/<int:pk>/', views_catalog.cupom_editar, name='cupom_editar'),
    path('cupons/<int:pk>/remover/', views_catalog.cupom_remover, name='cupom_remover'),

    path('fretes/', views_catalog.fretes_list, name='fretes'),
    path('fretes/novo/', views_catalog.frete_novo, name='frete_novo'),
    path('fretes/<int:pk>/', views_catalog.frete_editar, name='frete_editar'),
    path('fretes/<int:pk>/remover/', views_catalog.frete_remover, name='frete_remover'),

    path('posts/', views_catalog.posts_list, name='posts'),
    path('posts/novo/', views_catalog.post_novo, name='post_novo'),
    path('posts/<int:pk>/', views_catalog.post_editar, name='post_editar'),
    path('posts/<int:pk>/remover/', views_catalog.post_remover, name='post_remover'),

    path('avaliacoes/', views_extra.avaliacoes_list, name='avaliacoes'),
    path('avaliacoes/<int:pk>/aprovar/', views_extra.avaliacao_aprovar, name='avaliacao_aprovar'),
    path('avaliacoes/<int:pk>/remover/', views_extra.avaliacao_remover, name='avaliacao_remover'),

    path('indicacoes/', views_extra.indicacoes_list, name='indicacoes'),

    path('configuracoes/', views.configuracoes, name='configuracoes'),
]
