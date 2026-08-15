import unicodedata, re
from django.db import transaction
from core.models import Category, Product
def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode('ascii')
    s = re.sub(r'[^\w\s-]', '', s).strip().lower()
    return re.sub(r'[-\s]+', '-', s)
@transaction.atomic
def seed():
    cats = [('Capas e Peliculas','capas-peliculas','smartphone',1),('Carregadores','carregadores','zap',2),('Cabos e Adaptadores','cabos-adaptadores','cable',3),('Fones de Ouvido','fones','headphones',4),('Suporte e Carros','suporte-carros','car',5),('Power Banks','power-banks','battery-charging',6)]
    cm = {}
    for name,slug,icon,order in cats:
        c,_ = Category.objects.get_or_create(slug=slug, defaults={'name':name,'icon':icon,'order':order})
        cm[slug]=c
    prods = {
        'capas-peliculas':[('Capa Transparente Premium',29.90,40,'Capa flexivel a prova de quedas, bordas reforcadas.'),('Pelicula de Vidro Temperado 9H',19.90,120,'Protecao total anti-riscos, toque sensivel.'),('Capa Flip Couro Slim',49.90,25,'Estilo e protecao com suporte para apoio.'),('Pelicula Privacy 360',34.90,30,'Impede olhares laterais em locais publicos.')],
        'carregadores':[('Carregador Turbo 20W USB-C',59.90,50,'Carga rapida segura para a maioria dos modelos.'),('Carregador Veicular 30W',39.90,35,'Duas saidas USB-C + USB-A para o carro.'),('Carregador Sem Fio 15W',89.90,20,'Base magnetica com indicador LED.'),('Carregador Desktop 4 Portas',79.90,18,'Carrega 4 aparelhos simultaneamente.')],
        'cabos-adaptadores':[('Cabo USB-C 1m Trancado',24.90,80,'Super-resistente, suporte a dados e carga.'),('Cabo Lightning 1.5m',29.90,60,'Compativel, longo e duravel.'),('Adaptador USB-C p/ 3.5mm',19.90,45,'Use fones com fio em celulares sem entrada.'),('Adaptador USB-C p/ HDMI 4K',69.90,22,'Espelhe a tela em TV e monitor 4K.')],
        'fones':[('Fone Bluetooth TWS Mini',119.90,30,'Compacto, grave reforcado, estojos com carga.'),('Fone Headset Gaming',149.90,15,'Microfone com cancelamento, RGB.'),('Fone In-Ear com Fio',39.90,70,'Som limpo e confortavel para o dia a dia.'),('Fone Bluetooth Over-Ear',199.90,12,'Cancelamento de ruido ativo (ANC).')],
        'suporte-carros':[('Suporte Veicular Magnetico',44.90,40,'Fixacao forte no painel ou saida de ar.'),('Suporte de Mesa Ajustavel',34.90,28,'Para video-chamadas e leitura.'),('Suporte Quadro Giraotorio 360',39.90,25,'Gira e inclina para qualquer angulo.'),('Suporte Ventosa Para Para-Brisa',49.90,18,'Preso firmemente no vidro do carro.')],
        'power-banks':[('Power Bank 10.000mAh Slim',99.90,30,'Carrega 2x o celular, cabe no bolso.'),('Power Bank 20.000mAh Fast',159.90,20,'Carga rapida para dois aparelhos.'),('Power Bank Solar 15.000mAh',199.90,10,'Recarrega com luz solar em emergencias.'),('Power Bank com Cabo Integrado',119.90,25,'Nao esqueca o cabo: vai embutido.')],
    }
    for slug,items in prods.items():
        c = cm[slug]
        for name,price,stock,desc in items:
            Product.objects.get_or_create(slug=slug+'-'+slugify(name), defaults={'name':name,'description':desc,'price':price,'stock':stock,'icon':c.icon,'category':c,'featured':stock>25})
