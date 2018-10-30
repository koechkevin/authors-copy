import json
import copy
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse as api_reverse
from rest_framework import status

from authors import settings
from .base_tests import BaseTest

class ArticlesSearchTest(BaseTest):
    """
    Tests searching of articles
    """
    def setUp(self):
        """
        Setup the user and article for the tests
        """
        super().setUp()
        articles = [
            {
                'article': {
                    'title': 'One',
                    'description': 'This is a test article one',
                    'body': 'This is the whole article body',
                    'tags': ['tech', 'math', 'science']
                }
            },
            {
                'article': {
                    'title': 'Title',
                    'description': 'This is a test article',
                    'body': 'This is the whole article body',
                    'tags': ['tech', 'math', 'science']
                }
            }
        ]

        for article in articles:
            self.create_article(article=article)

        self.author_token = self.create_and_login_user()
        self.articles_url = api_reverse('articles:articles')

    def test_user_can_filter_articles_with_tags(self):
        """Test a user can get a rating on an article"""
        resp = self.client.get(self.articles_url+'?tag=math')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(resp.content)['article']['count'], 2)
        
    def test_user_can_filter_articles_with_title(self):
        """Test a user can get a rating on an article"""
        resp = self.client.get(self.articles_url+'?title=Title')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(resp.content)['article']['count'], 1)

    def test_user_can_filter_articles_with_author(self):
        """Test a user can get a rating on an article"""
        resp = self.client.get(self.articles_url+'?author='+self.user['user']['username'])

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(resp.content)['article']['count'], 2)

    def test_user_can_search_articles(self):
        """Test a user can get a rating on an article"""
        resp = self.client.get(self.articles_url+'?search=One')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(resp.content)['article']['count'], 1)
