from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse as api_reverse
from rest_framework import status
from authors.apps.authentication.models import UserManager


class AuthenticationTest(APITestCase):
    """
    User authentication test cases
    """
    def setUp(self):
        """
        Method for setting up user
        """
        self.url = api_reverse('authentication:user-registration')
        self.user =  { 
            'user' : { 
                'username': 'janeDoe', 
                'email': 'jane@doe.com', 
                'password': 'janedoe123', 
            }
        }

    def test_user_can_signup(self):
        """
        Test API can successfully register a new user
        """
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(b'go to your email and click the confirmation link', response.content)
    
    def test_user_cannot_signup_without_email(self):
        """
        Test API cannot register user without email
        """
        del self.user['user']['email']
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Email is required', response.content)

    def test_user_cannot_signup_with_invalid_email(self):
        """
        Test API cannot register user with an invalid email format
        """
        self.user['user']['email'] = 'NOT-AN-EMAIL'
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Enter a valid email address', response.content)

    def test_user_cannot_signup_without_password(self):
        """
        Test API cannot register user without password
        """
        del self.user['user']['password']
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Password is required', response.content)

    def test_user_cannot_signup_with_short_password(self):
        """
        Test api cannot register user with a password of less than 8 characters
        """
        self.user['user']['password'] = 'abc'
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Password must have at least 8 characters', 
                response.content)

    def test_user_cannot_signup_without_alphanumeric_password(self):
        """
        Test API cannot register user with a non-alphanumeric password
        """
        self.user['user']['password'] = 'abcdefghijk'
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Password must have a number and a letter', 
                response.content)

    def test_user_cannot_signup_without_username(self):
        """
        Test API cannot register user without a username
        """
        del self.user['user']['username']
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Username is required', response.content)

    def test_user_cannot_signup_with_wrong_username(self):
        """
        User cannot login with username with a space
        """
        self.user['user']['username'] = 'username with space'
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Username cannot have a space', response.content)

    def test_user_cannot_signup_with_short_username(self):
        """
        Test api cannot register user with username of less than 4 characters
        """
        self.user['user']['username'] = 'abc'
        response = self.client.post(self.url, self.user, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Username must have at least 4 characters', 
                response.content)

