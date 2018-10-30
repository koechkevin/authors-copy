from rest_framework.reverse import reverse as API_Reverse
from rest_framework import status
import json

from authors.apps.articles.helpers import get_time_to_read_article
from authors.apps.articles.tests.base_tests import BaseTest
from authors.apps.articles.models import ArticlesModel


class ArticleTests(BaseTest):
    def test_article_returns_url(self):
        """This method tests whether the API returns url"""
        self.create_user()
        self.activate_user()
        token = self.login_user()
        response = self.client.post(self.url, self.article, format="json", HTTP_AUTHORIZATION=token)
        self.assertIn("url", json.dumps(response.data))

    def test_if_article_returns_facebook_url(self):
        """This method tests whether the API returns facebook url"""
        self.create_user()
        self.activate_user()
        token = self.login_user()
        response = self.client.post(self.url, self.article, format="json", HTTP_AUTHORIZATION=token)
        self.assertIn("facebook", json.dumps(response.data))



    def test_if_article_returns_linkedin_url(self):
        """This method tests whether the API returns linkedin url"""
        self.create_user()
        self.activate_user()
        token = self.login_user()
        response = self.client.post(self.url, self.article, format="json", HTTP_AUTHORIZATION=token)
        self.assertIn("Linkedin", json.dumps(response.data))

    def test_if_article_returns_twitter_url(self):
        """This method tests whether the API returns twitter url"""
        self.create_user()
        self.activate_user()
        token = self.login_user()
        response = self.client.post(self.url, self.article, format="json", HTTP_AUTHORIZATION=token)
        self.assertIn("twitter", json.dumps(response.data))

    def test_if_article_returns_mail_url(self):
        """This method tests whether the API returns mail url"""
        self.create_user()
        self.activate_user()
        token = self.login_user()
        response = self.client.post(self.url, self.article, format="json", HTTP_AUTHORIZATION=token)
        self.assertIn("mail", json.dumps(response.data))
