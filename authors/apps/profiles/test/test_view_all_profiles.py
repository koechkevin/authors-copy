from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework import status
import json
from ..models import Profile
from ...authentication.models import User

class TestProfileListApi(APITestCase):
    def setUp(self):
        """
        create four users, the user on session and three other users to whom the user
        on session can see.
        """
        self.url = reverse('profiles:view_all')
        register_url = reverse('authentication:user-registration')
        login_url = reverse('authentication:user_login')
        def create_user(username, email, password):
            user =  {
                    'user' : {
                        'username': username,
                        'email': email,
                        'password': password
                    }
                }
            self.client.post(register_url,user, format="json")
            user = User.objects.get(email=email)
            user.is_active = True
            user.save()

        create_user('username', 'email@email.com', 'password123')
        create_user('kevin', 'koech@gmail.com', 'Kev12345')
        create_user('kibitok', 'koechkevin@gmail.com', 'Kev12345')
        create_user('koech', 'koechkevin92@gmail.com', 'Kev12345')
        user =  {
                    'user' : {
                        'email': 'email@email.com',
                        'password': 'password123'
                    }
                }
        response = self.client.post(login_url,user, format="json")
        self.token = json.loads(response.content)['user']['token']

    def test_user_can_view_profiles(self):
        """a user cannot see owns profile on the list"""
        self.client.credentials(HTTP_AUTHORIZATION=self.token)
        response = self.client.get(self.url)
        self.assertTrue(json.loads(response.content)['profiles'], True)
        content = json.loads(response.content)['profiles']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(content),3)

    def test_unauthorized_user_cannot_view(self):
        response =self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content)['detail']
        self.assertTrue(content, True)
        self.assertEqual(content, 'Authentication credentials were not provided.')

    def test_wrong_url(self):
        response =self.client.get('/api/profile')
        self.assertEqual(response.status_code, 404)
