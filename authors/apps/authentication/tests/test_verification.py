from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework import status
from authors.apps.authentication.models import User
from django.core import mail
from django.urls import reverse
from authors.apps.authentication.token import generate_token


class AccountVerification(APITestCase):
    """
    Test for account verification
    """

    def setUp(self):
        """
        Define globals.
        """
        self.client = APIClient()
        self.registration_url = reverse('authentication:user-registration')
        self.user_data = {
            'user' : { 
                'username': 'janeDoe', 
                'email': 'jane@doe.com', 
                'password': 'janedoe123', 
            }
        }

    def test_confirmation_mail(self):
        """
        Test for sending of confirmation mail
        """
        # More on Outbox objects can be found in the following link
        # https://docs.djangoproject.com/en/dev/topics/email/#django.core.mail.EmailMessage

        self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Please verify your account", mail.outbox[0].body)

    def test_account_verification(self):
        """
        Test for successful account verification
        """
        self.client.post(self.registration_url, self.user_data, format='json')
        user = self.user_data['user']
        token = generate_token(user['username'])
        response = self.client.get(reverse("authentication:verify", args=[token]))
        user = User.objects.get(username=user['username'])
        self.assertTrue(user.is_active)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fail_verification(self):
        """
        Test for user verification failure
        :return:
        """
        self.client.post(self.registration_url, self.user_data, format='json')
        user = self.user_data['user']
        token = generate_token(user['username'])
        response = self.client.get(reverse("authentication:verify", args=[token+"invalid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Invalid', response.content)
