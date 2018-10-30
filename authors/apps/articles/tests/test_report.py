from rest_framework import status
import json

from authors.apps.articles.tests.base_tests import BaseTest, API_Reverse


class ReportArticlesTests(BaseTest):
    """This class tests the report articles functionality"""

    def setUp(self):
        """This method sets up the tests"""
        super().setUp()
        self.reporter = {
            "user": {
                "username": "reporting_user",
                "password": "reporting134",
                "email": "reporting@test.com"
            }
        }
        self.reporter_token = self.create_and_login_user(user=self.reporter)
        self.author_token = self.create_and_login_user(user=self.user)
        self.article_slug = self.create_article(token=self.author_token)
        self.report_url = API_Reverse(
            'articles:report',
            {self.article_slug: 'slug'}
        )
        self.report = {
            "report": {
                "report_msg": "I don't like this article because"
            }
        }

    def test_user_can_report_an_article(self):
        """This method tests if a user can report an article"""
        self.client.credentials(HTTP_AUTHORIZATION=self.reporter_token)
        response = self.client.post(self.report_url,
                                    data=self.report,
                                    format='json')
        self.assertIn('An email has been sent to the admin with your request', json.dumps(response.data))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_report_their_own_article(self):
        """This method tests is a user can report they own article"""
        response = self.client.post(self.report_url,
                                    data=self.report,
                                    format='json')
        self.assertIn('You cannot report your own article', json.dumps(response.data))
        self.assertIn('errors', json.dumps(response.data))
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_user_cannot_spam_with_report(self):
        """This method tests if a user cannot post multiple reports of the same article"""
        self.client.credentials(HTTP_AUTHORIZATION=self.reporter_token)
        self.client.post(self.report_url, data=self.report,format='json')
        self.client.post(self.report_url, data=self.report, format='json')
        self.client.post(self.report_url, data=self.report, format='json')
        response = self.client.post(self.report_url, data=self.report, format='json')
        self.assertIn('You cannot report this article multiple times', json.dumps(response.data))
        self.assertIn('errors', json.dumps(response.data))
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)








