from django import forms
from django.contrib.auth import authenticate

from core.models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'ga4_measurement_id', 'meta_pixel_id',
            'whatsapp_cloud_api_token', 'whatsapp_cloud_phone_id',
        ]
        widgets = {
            'whatsapp_cloud_api_token': forms.PasswordInput(render_value=True),
        }
        help_texts = {
            'ga4_measurement_id': 'Formato G-XXXXXXX, do Google Analytics > Fluxos de dados.',
            'meta_pixel_id': 'ID numérico do pixel, do Gerenciador de Eventos Meta.',
            'whatsapp_cloud_api_token': 'Token permanente do app WhatsApp Cloud API (Meta).',
            'whatsapp_cloud_phone_id': 'ID do número de telefone (não é o número em si).',
        }


class PanelLoginForm(forms.Form):
    username = forms.CharField(label='Usuário')
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get('username')
        password = cleaned.get('password')
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None or not user.is_staff:
                raise forms.ValidationError('Usuário ou senha incorretos.')
            cleaned['user'] = user
        return cleaned
