from django.urls import path
from store import feeds, views
app_name = 'store'
urlpatterns = [
    path('', views.home, name='home'),
    path('produtos/', views.produtos, name='produtos'),
    path('produto/<slug:slug>/', views.produto_detalhe, name='produto'),
    path('produto/<slug:slug>/avaliar/', views.avaliar_produto, name='avaliar'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('produto/<slug:slug>/add/', views.add_cart, name='add_cart'),
    path('carrinho/<str:cart_key>/update/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedido/<str:code>/', views.pedido, name='pedido'),
    path('indicar/', views.indicar, name='indicar'),
    path('blog/', views.blog_lista, name='blog_lista'),
    path('blog/<slug:slug>/', views.blog_post, name='blog_post'),
    path('produtos.xml', feeds.produtos_xml, name='feed_produtos'),
]
