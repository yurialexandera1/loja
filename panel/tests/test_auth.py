from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class PanelAccessTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse('panel:dashboard'))

        self.assertRedirects(response, f"{reverse('panel:login')}?next={reverse('panel:dashboard')}")

    def test_non_staff_user_is_redirected_to_login(self):
        User.objects.create_user(username='cliente', password='senha12345')
        self.client.login(username='cliente', password='senha12345')

        response = self.client.get(reverse('panel:dashboard'))

        self.assertRedirects(response, f"{reverse('panel:login')}?next={reverse('panel:dashboard')}")

    def test_staff_user_reaches_dashboard(self):
        User.objects.create_user(username='yuri', password='senha12345', is_staff=True)
        self.client.login(username='yuri', password='senha12345')

        response = self.client.get(reverse('panel:dashboard'))

        self.assertEqual(response.status_code, 200)


class PanelLoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='yuri', password='senha12345', is_staff=True)

    def test_valid_credentials_log_in_and_redirect_to_dashboard(self):
        response = self.client.post(
            reverse('panel:login'), {'username': 'yuri', 'password': 'senha12345'}
        )

        self.assertRedirects(response, reverse('panel:dashboard'))

    def test_invalid_credentials_show_error_without_logging_in(self):
        response = self.client.post(
            reverse('panel:login'), {'username': 'yuri', 'password': 'errada'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'incorretos')

    def test_non_staff_credentials_are_rejected(self):
        User.objects.create_user(username='cliente', password='senha12345')

        response = self.client.post(
            reverse('panel:login'), {'username': 'cliente', 'password': 'senha12345'}
        )

        self.assertContains(response, 'incorretos')

    def test_logout_ends_session(self):
        self.client.login(username='yuri', password='senha12345')

        self.client.post(reverse('panel:logout'))
        response = self.client.get(reverse('panel:dashboard'))

        self.assertRedirects(response, f"{reverse('panel:login')}?next={reverse('panel:dashboard')}")
