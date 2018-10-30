from rest_framework.test import APITestCase, APIClient
from rest_framework.reverse import reverse as API_Reverse
from django.urls import reverse

from authors.apps.authentication.token import generate_token


class BaseTest(APITestCase):
    """This class provides a base for other tests"""

    def setUp(self):
        self.url = API_Reverse('articles:articles')
        self.client = APIClient()
        self.unauthorised_client = APIClient()
        self.signup_url = API_Reverse('authentication:user-registration')    
        self.login_url = API_Reverse('authentication:user_login')    
        
        self.user = {
            "user": {
                "username": "test_user",
                "password": "testing123",
                "email": "test@test.com"
            }
        }

        self.user2 = {
            "user": {
                "username": "test_user2",
                "password": "testing123",
                "email": "test2@test.com"
            }
        }

        self.article = {
            "article": {
                "title": "test article",
                "description": "This is test description",
                "body": "This is a test body",
                "tags": ["test", "tags"]
            }
        }

        self.comment = {
            "comment": {
                "body": "This is a test comment body."
            }
        }

    def create_user(self, user=None):
        if not user:
            user = self.user
        response = self.client.post(self.signup_url, user, format='json')
        return response

    def activate_user(self, user=None):
        """Activate user after login"""
        if not user:
            user = self.user
        self.client.post(self.signup_url, user, format='json')
        token = generate_token(user['user']['username'])
        self.client.get(reverse("authentication:verify", args=[token]))


    def login_user(self, user=None):
        """This will login an existing user"""
        if not user: 
            user = self.user
        response = self.client.post(self.login_url, user, format='json')
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=token)
        return token

    def create_and_login_user(self, user=None):
        if not user:
            user = self.user
        self.create_user(user=user)
        self.activate_user(user=user)
        return self.login_user(user=user)

    def create_article(self, token=None, article=None):
        if not token:
            self.create_user()
            self.activate_user()
            token = self.login_user()
        if not article:
            article = self.article
        response = self.client.post(self.url, article, format='json', HTTP_AUTHORIZATION=token)
        slug = response.data['slug']

        return slug

    def single_article_details(self):
        slug = self.create_article()
        url = API_Reverse('articles:article-details', {slug: 'slug'})
        return url

    def create_comment(self):
        slug = self.create_article()
        post_url = API_Reverse('articles:comments', {slug: 'slug'})
        post_response = self.client.post(post_url, self.comment, format='json')
        id = post_response.data['id']
        return id, slug

    def update_comment(self, id, slug, new_comment):
        url = API_Reverse('articles:comment-details', {slug: 'slug', id: 'id'})
        response = self.client.put(url, data={'comment': {'body': new_comment}}, format='json')
        return response

    def create_comment_like(self):
        slug = self.create_article()
        post_url = API_Reverse('articles:comments', {slug: 'slug'})
        post_response = self.client.post(post_url, self.comment, format='json')
        id = post_response.data['id']
        return id
