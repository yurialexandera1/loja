import re

from django import forms

SHIPPING = [
    ('padrao', 'Padrao — R$ 15,00 (5-8 dias)'),
    ('expresso', 'Expresso — R$ 30,00 (1-3 dias)'),
    ('gratis', 'Retirar / Gratis acima de R$ 199'),
]

ZIP_RE = re.compile(r'^\d{5}-?\d{3}$')
COUPON_RE = re.compile(r'^[A-Za-z0-9_-]*$')


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(label='Nome completo', max_length=200)
    email = forms.EmailField(label='E-mail')
    phone = forms.CharField(label='Telefone / WhatsApp', max_length=40, required=False)
    address = forms.CharField(label='Endereco', max_length=300)
    city = forms.CharField(label='Cidade', max_length=120)
    zip = forms.CharField(label='CEP', max_length=20)
    shipping_option = forms.ChoiceField(label='Frete', choices=SHIPPING)
    coupon_code = forms.CharField(label='Cupom de desconto', max_length=32, required=False)

    def clean_zip(self):
        value = self.cleaned_data['zip'].strip()
        if not ZIP_RE.match(value):
            raise forms.ValidationError('Informe um CEP valido no formato 00000-000.')
        return value

    def clean_phone(self):
        value = self.cleaned_data.get('phone', '').strip()
        if not value:
            return value
        digits = re.sub(r'\D', '', value)
        if not (10 <= len(digits) <= 11):
            raise forms.ValidationError('Informe um telefone valido com DDD (10 ou 11 digitos).')
        return value

    def clean_coupon_code(self):
        value = self.cleaned_data.get('coupon_code', '').strip()
        if not value:
            return value
        if not COUPON_RE.match(value):
            raise forms.ValidationError('Cupom invalido: use apenas letras, numeros, hifen ou underline.')
        return value.upper()


class ReviewForm(forms.Form):
    author_name = forms.CharField(label='Seu nome', max_length=120)
    rating = forms.TypedChoiceField(
        label='Nota',
        coerce=int,
        choices=[(n, f'{n} estrela{"s" if n != 1 else ""}') for n in range(5, 0, -1)],
    )
    comment = forms.CharField(label='Comentário', widget=forms.Textarea, min_length=5, max_length=1000)


class ReferralSignupForm(forms.Form):
    owner_name = forms.CharField(label='Seu nome', max_length=200)
    owner_email = forms.EmailField(label='Seu e-mail')
