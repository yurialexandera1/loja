from django import forms
from django.contrib.auth import authenticate


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
