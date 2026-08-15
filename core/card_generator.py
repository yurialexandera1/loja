"""Gerador de imagem de produto a partir de foto crua + dados reais do banco.

Dois modos:
- site: foto limpa sobre fundo da marca + logo discreto no canto (sem preco/CTA
  desenhados, porque o card HTML do site ja mostra nome/preco/botao de verdade —
  desenhar de novo na imagem duplica a informacao).
- social: peca completa pra WhatsApp/Instagram (logo, titulo, preco, PIX, CTA),
  no mesmo estilo das pecas ja usadas na loja.

Nao gera nem inventa produto: usa a foto real enviada e os dados reais do
Product (nome, preco, pix_price) ja existentes no banco.
"""
from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont, ImageOps

BRAND_GROUND = (250, 247, 243)
BRAND_SURFACE = (242, 235, 227)
BRAND_INK = (23, 18, 16)
BRAND_ACCENT = (217, 83, 30)
BRAND_ACCENT_DEEP = (166, 58, 17)
BRAND_GOOD = (44, 115, 67)

FONT_BOLD = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
FONT_REGULAR = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'

CANVAS = 1000


def _font(path, size):
    return ImageFont.truetype(path, size)


def _fit_photo(photo: Image.Image, box_w: int, box_h: int) -> Image.Image:
    photo = ImageOps.exif_transpose(photo.convert('RGBA'))
    fitted = ImageOps.contain(photo, (box_w, box_h))
    canvas = Image.new('RGBA', (box_w, box_h), (0, 0, 0, 0))
    canvas.paste(fitted, ((box_w - fitted.width) // 2, (box_h - fitted.height) // 2), fitted)
    return canvas


def _rounded_rect(draw, box, radius, **kwargs):
    draw.rounded_rectangle(box, radius=radius, **kwargs)


def _paste_logo(canvas: Image.Image, logo: Image.Image, pos, max_h):
    logo = logo.convert('RGBA')
    ratio = max_h / logo.height
    logo = logo.resize((int(logo.width * ratio), max_h))
    canvas.paste(logo, pos, logo)


def generate_site_card(photo: Image.Image, logo: Image.Image) -> Image.Image:
    """Foto limpa + logo discreto — usada no site, sem duplicar preco/CTA."""
    canvas = Image.new('RGB', (CANVAS, CANVAS), BRAND_GROUND)
    draw = ImageDraw.Draw(canvas)
    margin = 40
    _rounded_rect(draw, (margin, margin, CANVAS - margin, CANVAS - margin), 32, fill=BRAND_SURFACE)

    inner = _fit_photo(photo, CANVAS - margin * 2 - 80, CANVAS - margin * 2 - 80)
    canvas.paste(inner, (margin + 40, margin + 40), inner)

    _paste_logo(canvas, logo, (CANVAS - margin - 120, CANVAS - margin - 56), 40)
    return canvas


def generate_social_card(photo: Image.Image, logo: Image.Image, name: str, price: str, pix_price: str) -> Image.Image:
    """Peca completa (logo, titulo, preco, PIX, CTA WhatsApp) pra divulgacao."""
    canvas = Image.new('RGB', (CANVAS, CANVAS), BRAND_GROUND)
    draw = ImageDraw.Draw(canvas)

    frame_box = (60, 40, 660, 640)
    _rounded_rect(draw, frame_box, 28, outline=BRAND_ACCENT, width=4)
    inner = _fit_photo(photo, frame_box[2] - frame_box[0] - 40, frame_box[3] - frame_box[1] - 40)
    canvas.paste(inner, (frame_box[0] + 20, frame_box[1] + 20), inner)

    _paste_logo(canvas, logo, (CANVAS - 260, 40), 70)
    draw.text((CANVAS - 178, 118), 'CASE_SEE', font=_font(FONT_BOLD, 30), fill=BRAND_INK, anchor='mm')

    title_font = _font(FONT_BOLD, 52)
    draw.text((60, 700), name.upper(), font=title_font, fill=BRAND_INK)

    bar_top = 800
    draw.rectangle((0, bar_top, CANVAS, CANVAS), fill=BRAND_INK)
    draw.text((40, bar_top + 24), 'POR APENAS', font=_font(FONT_BOLD, 26), fill=(255, 255, 255))
    draw.text((40, bar_top + 60), f'R$ {price}', font=_font(FONT_BOLD, 64), fill=BRAND_ACCENT)
    draw.text((40, bar_top + 140), f'R$ {pix_price} no PIX', font=_font(FONT_REGULAR, 26), fill=BRAND_GOOD)

    cta_box = (520, bar_top + 30, CANVAS - 40, CANVAS - 30)
    _rounded_rect(draw, cta_box, 16, fill=BRAND_ACCENT)
    draw.text(
        ((cta_box[0] + cta_box[2]) // 2, (cta_box[1] + cta_box[3]) // 2),
        'PEÇA NO\nWHATSAPP', font=_font(FONT_BOLD, 24), fill=(255, 255, 255), anchor='mm', align='center'
    )
    return canvas


def to_jpeg_bytes(image: Image.Image, quality=90) -> bytes:
    buf = io.BytesIO()
    image.convert('RGB').save(buf, format='JPEG', quality=quality)
    return buf.getvalue()
