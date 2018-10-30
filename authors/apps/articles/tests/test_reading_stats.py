import json
from rest_framework import status

from authors.apps.articles.models import ArticleStat, Comment
from authors.apps.articles.tests.base_tests import BaseTest


class StatsTestCase(BaseTest):
    """
    Class for reading stats test cases
    """

    def test_views_increase_upon_getting_article(self):
        """
        Method asserts that count increases after every view
        """
        old_count = ArticleStat.objects.count()
        url = self.single_article_details()
        self.client.get(url, format='json')
        new_count = ArticleStat.objects.count()
        self.assertNotEqual(old_count, new_count)

    def test_comments_increase_upon_posting_comment(self):
        """
        Method asserts that count increases after comment is posted
        """
        old_count = Comment.objects.count()
        self.create_comment()
        new_count = Comment.objects.count()
        self.assertNotEqual(old_count, new_count)

    def test_count_increases_if_user_comments_multiple_times(self):
        """
        Method asserts that count increases after multiple comments are posted
        """
        self.create_comment()
        old_count = Comment.objects.count()
        self.create_comment()
        new_count = Comment.objects.count()
        self.assertNotEqual(old_count, new_count)

    def test_views_increase_upon_getting_article_multiple_times(self):
        """
        Method asserts that count increases after multiple views by same user
        """
        url = self.single_article_details()
        self.client.get(url, format='json')
        old_count = ArticleStat.objects.count()
        url = self.single_article_details()
        self.client.get(url, format='json')
        new_count = ArticleStat.objects.count()
        self.assertNotEqual(old_count, new_count)          