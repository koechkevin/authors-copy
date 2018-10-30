from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse as api_reverse
from rest_framework import status

User = get_user_model()
class SocialAuthSignUp(APITestCase):
    def setUp(self):

        self.social_url=api_reverse('authentication:social_sign_up')

        user_object = User(
            username='testuser',
            email='test@gmail.com',
            is_active=True
            )
        user_object.set_password('randompassword')
        user_object.save()

    def test_no_provider(self):
        access_token = 'EAAe6UMnIZBRoBAG9GEsj3TwlzejSsWf4s2r0RmG8BMpwqJxx3dwCWAremGJHEQHiMJa2ro2Nk68zeqf7Pwy9gtTrqBdHODT5XlYlL2mpfNc3pBamkHoclJZCSty3WZCGh0qvP6kZCO5nse54tbtfh0YACsU3hdGk8XjyrRZBxIcA2Cr5C9nOvRPvnDZA2DURoHuTrvuGda7BAJPXKTfrZCPJ2bPUAqnW836eNWpldIzJLMA8GrBzJLN'
        data={"access_token":access_token}
        resp=self.client.post(self.social_url,data=data)
        self.assertEqual(resp.status_code,status.HTTP_400_BAD_REQUEST)

    def test_for_no_token(self):
        provider = 'google-oauth2'
        data={"provider":provider}
        resp=self.client.post(self.social_url,data=data)
        self.assertEqual(resp.status_code,status.HTTP_400_BAD_REQUEST)


    
