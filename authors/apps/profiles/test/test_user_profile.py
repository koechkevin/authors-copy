from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from ..models import Profile


from authors.apps.authentication.models import UserManager
from authors.apps.authentication.token import generate_token



class ProfileTest(APITestCase):
    """
    User authentication test cases
    """
    def setUp(self):
        """
        Method for setting up user
        """
        self.user =  {
            'user' : {
                'username': 'janeDoe',
                'email': 'jane@doe.com',
                'password': 'janedoe123',
            }
        }

        self.login_url = reverse('authentication:user_login')
        self.url_register = reverse('authentication:user-registration')
        self.url_profile = reverse('profiles:user-profile', kwargs={"username": self.user['user']['username']})

    def registration(self):
        response = self.client.post(self.url_register, self.user, format='json')
        return response
    def activate_user(self):
        """Activate user after login"""
        self.client.post(self.url_register, self.user, format='json')
        user = self.user['user']
        token = generate_token(user['username'])
        self.client.get(reverse("authentication:verify", args=[token]))
    def login_user(self):
        """This will login an existing user"""
        response = self.client.post(self.login_url, self.user, format='json')
        token = response.data['token']
        return token

    def test_model_can_create_user_profile(self):
        """
        Test API can successfully register a new user
        """
        old_count = Profile.objects.count()
        response = self.client.post(self.url_register, self.user, format='json')
        new_count = Profile.objects.count()
        self.assertNotEqual(old_count, new_count)

    def test_get_user_profile(self):
        self.registration()
        self.activate_user()
        token = self.login_user()
        self.client.post(self.url_register, self.user, format='json')
        response = self.client.get(self.url_profile, format='json', HTTP_AUTHORIZATION=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_profile(self):
        self.registration()
        self.activate_user()
        token = self.login_user()
        self.client.post(self.url_register, self.user, format='json')
        response = self.client.put(self.url_profile,
        {
            'user' : {
                'username': 'jDoe',
                'bio': 'I am that guy'
            }
        }, format='json', HTTP_AUTHORIZATION=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_profile_short_username_format(self):
        self.registration()
        self.activate_user()
        token = self.login_user()
        self.client.post(self.url_register, self.user, format='json')
        response = self.client.put(self.url_profile,
        {
            'user' : {
                'username': 'jDo',
                'bio': 'I am that guy'
            }
        }, format='json', HTTP_AUTHORIZATION=token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Username must have at least 4 characters', response.content)

    def test_update_profile_no_username(self):
        self.registration()
        self.activate_user()
        token = self.login_user()
        self.client.post(self.url_register, self.user, format='json')
        response = self.client.put(self.url_profile,
        {
            'user' : {
                'username': '',
                'bio': 'I am that guy'
            }
        }, format='json', HTTP_AUTHORIZATION=token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'This field may not be blank', response.content)

    def test_update_profile_spaced_username(self):
        self.registration()
        self.activate_user()
        token = self.login_user()
        self.client.post(self.url_register, self.user, format='json')
        response = self.client.put(self.url_profile,
        {
            'user' : {
                'username': 'ia o',
                'bio': 'I am that guy'
            }
        }, format='json', HTTP_AUTHORIZATION=token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Username cannot have a space', response.content)

    def test_update_profile_blank_bio(self):
        self.registration()
        self.activate_user()
        token = self.login_user()
        self.client.post(self.url_register, self.user, format='json')
        response = self.client.put(self.url_profile,
        {
            'user' : {
                'username': 'iano',
                'bio': ''
            }
        }, format='json', HTTP_AUTHORIZATION=token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'This field may not be blank', response.content)

    def test_update_profile_spaces_only_in__bio(self):
        self.registration()
        self.activate_user()
        token = self.login_user()
        self.client.post(self.url_register, self.user, format='json')
        response = self.client.put(self.url_profile,
        {
            'user' : {
                'username': 'iano',
                'bio': '  '
            }
        }, format='json', HTTP_AUTHORIZATION=token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'This field may not be blank', response.content)