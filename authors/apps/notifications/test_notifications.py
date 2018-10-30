from authors.apps.articles.tests.base_tests import BaseTest
from rest_framework import status
from rest_framework.reverse import reverse
from django.core import mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from authors.apps.articles.models import ArticlesModel

class TestUserNotifications(BaseTest):
    """"
    Test for users notifications
    """

    def setUp(self):
        super().setUp()
        self.follower = {"user": {
            "username": "john",
            "email": "johndoe@gmail.com",
            "password": "1234John"
            }
        }

        self.author_token = self.create_and_login_user()
        self.subscribe = reverse('notifications:subscribe')
        self.unsubscribe = reverse('notifications:unsubscribe')
        self.all_notifications = reverse('notifications:notification')
        self.follow_url = reverse("profiles:follow", kwargs={"username": self.user['user']['username']})

    def test_notifications_subscription(self):
        resp = self.client.get(self.subscribe)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_notifications_unsubscription(self):
        self.client.get(self.subscribe)
        resp = self.client.get(self.unsubscribe)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_all_notifications(self):
        resp = self.client.get(self.all_notifications)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('notifications', resp.data)

    def test_for_double_subscription(self):
        # first subscription
        self.client.get(self.subscribe)
        # 2nd subscription
        resp = self.client.get(self.subscribe)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'already subscribed', resp.content)

    def test_unsubscribe_while_not_subscribed(self):
        self.client.get(self.subscribe)
        self.client.get(self.unsubscribe)
        resp = self.client.get(self.unsubscribe)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'not subscribed', resp.content)

    def test_emailing_on_article_addition(self):
        # create user and get his token
        self.author_token = self.create_and_login_user()
        # create a follower
        self.create_and_login_user(self.follower)
        # follow user
        self.client.post(self.follow_url)
        # followed user create article
        self.slug = self.create_article(token=self.author_token)

        @receiver(post_save, sender=ArticlesModel)
        # This receiver handles notification creation immediately a new article is created.
        def notification(sender, instance=None, created=None, **kwargs):
            """
            Sends notification
            """
            if created:
                instance = self.slug
                return instance


