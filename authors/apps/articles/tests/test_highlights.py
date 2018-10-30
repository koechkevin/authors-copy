from rest_framework.test import APITestCase
from rest_framework.reverse import reverse as api_reverse
from rest_framework import status

from .base_tests import BaseTest
from authors.apps.articles.models import Highlighted


class HighlightingTests(BaseTest):
    """
    Highlight test cases
    """

    def setUp(self):
        """
        Setup user highlight and articles for tests
        """
        super().setUp()
        self.author_token = self.create_and_login_user()
        self.slug = self.create_article()
        self.highlight_url = api_reverse(
            'articles:highlighted', {self.slug: 'slug'})

        self.highlight = {
            "highlight": {
                "snippet": "This is",
                "index": 0
            }
        }

        self.highlight_and_comment = {
            "highlight": {
                "snippet": "This is",
                "comment": "Nice work man.",
                "index": 0
            }
        }

        self.highlight_update_comment = {
            "highlight": {
                "snippet": "This is",
                "comment": "Better luck next time",
                "index": 0
            }
        }

    def create_highlight(self, highlight=None):
        if not highlight:
            highlight = self.highlight
        response = self.client.post(
            self.highlight_url,
            highlight,
            'json',
            HTTP_AUTHORIZATION=self.author_token
        )

        return response

    # def update_highlight(self, higlight, id):
    #     response = self.client.put(
    #         self.highlight_url,
    #         higlight,
    #         'json',
    #         HTTP_AUTHORIZATION=self.author_token,
    #         id="id"
    #     )

    def test_user_create_highlight(self):
        """
        Test user can create highlight
        """
        response = self.create_highlight()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_highlights_added_to_model(self):
        """
        Test to verify highlight data is stored
        """
        old_count = Highlighted.objects.count()
        self.create_highlight()
        new_count = Highlighted.objects.count()
        self.assertNotEqual(new_count, old_count)

    def test_user_update_highlight_add_comment(self):
        """
        Test to verify if a user can update highlight
        """
        response = self.create_highlight()
        id = response.data["id"]
        url = api_reverse(
            'articles:highlighted', {self.slug: 'slug', id: "id"})
        response2 = self.client.put(
            url,
            self.highlight_and_comment,
            'json',
            HTTP_AUTHORIZATION=self.author_token
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_cannot_get_higlight(self):
        """Test that user cannot get highlights for a non existant article"""
        slug = "non-slug"
        url = api_reverse(
            'articles:highlighted', {slug: 'slug'}
            )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            
    def test_user_cant_highlight_twice(self):
        """
        Test to verify if a user can't post same highlight twice
        """
        self.create_highlight()
        response = self.create_highlight()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cant_highlight_comment_twice(self):
        """
        Test to verify that a user cant add same comment and highlight twice
        """
        self.create_highlight(self.highlight_and_comment)
        response = self.create_highlight(self.highlight_and_comment)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_non_existent_highlight(self):
        """
        Test to verify if a user cant add a non-existent highlight
        """
        response = self.create_highlight(
            {
                "highlight": {
                    "snippet": "Oh my",
                    "index": 0
                }
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_highlight_non_existent_article(self):
        """
        Test a user cant highlight a non-existent article
        """
        response = self.client.post(
            '/api/articles/another-failing-test/highlight/',
            self.highlight,
            'json',
            HTTP_AUTHORIZATION=self.author_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_highlight_article(self):
        """
        Test unauthenticated user cannot highlight an article
        """
        self.client.credentials(HTTP_AUTHORIZATION='')
        response = self.create_highlight()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_highlight_for_article(self):
        """
        Test user can get highlights for an article
        """
        self.create_highlight()
        response = self.client.get(self.highlight_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_article_no_highlights(self):
        """
        Test getting article with no highlights
        """
        response = self.client.get(self.highlight_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
