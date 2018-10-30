import copy
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse as api_reverse
from rest_framework import status

from authors import settings
from .base_tests import BaseTest

class RatingsTest(BaseTest):
    """
    Tests rating of an article
    """
    def setUp(self):
        """
        Setup the user, rating and article for the tests
        """
        super().setUp()
        self.rating =  {'rating': {'rating': 4}}

        self.rater = {
            "user": {
                "username": "rating_user",
                "password": "ratinguser134",
                "email": "rating@rater.com"
            }
        }
        self.author_token = self.create_and_login_user()
        self.article_slug = self.create_article(token=self.author_token)
        self.rater_token = self.create_and_login_user(user=self.rater)
        self.article_rating_url = api_reverse(
            'articles:ratings', 
            {self.article_slug: 'slug'}
        )

    def create_article_rating(self, rating=None):
        if not rating:
            rating = self.rating
        resp = self.client.post(
            self.article_rating_url, 
            rating, 
            'json', 
            HTTP_AUTHORIZATION=self.rater_token
        )

        return resp

    def update_article_rating(self, rating=None):
        if not rating:
            rating = self.rating
        resp = self.client.put(
            self.article_rating_url, 
            rating, 
            'json',
            HTTP_AUTHORIZATION=self.rater_token
        )

        return resp

    def test_user_can_rate_article(self):
        """A user can rate another user's article"""
        resp = self.client.post(
            self.article_rating_url, 
            self.rating, 
            'json', 
            HTTP_AUTHORIZATION=self.rater_token
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn(b'rating', resp.content)

    def test_user_can_get_rating_on_article(self):
        """Test a user can get a rating on an article"""
        self.create_article_rating()
        resp = self.client.get(self.article_rating_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b'rating', resp.content)
        
    def test_unauthenticated_user_can_get_rating_on_article(self):
        """Test unauthenticated user can get a rating on an article"""
        self.create_article_rating()
        resp = self.client.get(self.article_rating_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b'avg_rating', resp.content)
        
    def test_user_cannot_create_rating_without_value(self):
        """Rating value is required while rating"""
        del self.rating['rating']
        resp = self.create_article_rating()

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'The rating is required', resp.content)
        
    def test_user_cannot_create_rating_with_invalid_value(self):
        """Rating must be within a specified range"""
        self.rating['rating']['rating'] = settings.RATING_MIN - 1
        resp = self.create_article_rating()

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Rating cannot be less than', resp.content)

        self.rating['rating']['rating'] = settings.RATING_MAX + 1
        resp = self.create_article_rating()

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Rating cannot be more than', resp.content)
        
    def test_user_can_update_their_rating(self):
        """User can update their rating on an article"""
        resp = self.create_article_rating()

        self.rating['rating']['rating'] = 5
        resp = self.update_article_rating()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b'rating', resp.content)
        self.assertIn(b'5', resp.content)
        
    def test_user_cannot_update_nonexistant_rating(self):
        """Ensure a rating exists for it to be updated"""
        resp = self.update_article_rating()

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(b'rating', resp.content)
        self.assertIn(b'Rating not found', resp.content)

    def test_user_cannot_update_rating_for_nonexistant_article(self):
        """Check a user cannot update a rating for an article that does't exist"""

        url = api_reverse('articles:ratings', {'NOT-A-SLUG ':'slug'})
        resp = self.update_article_rating()

        resp = self.client.post(
            url, 
            self.rating, 
            'json', 
            HTTP_AUTHORIZATION=self.rater_token
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'No article found for the slug given', resp.content)

    def test_user_cannot_update_rating_with_invalid_values(self):
        """An update on a rating must be within specified range"""
        self.create_article_rating()

        self.rating['rating']['rating'] = settings.RATING_MAX + 1
        resp = self.update_article_rating()

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Rating cannot be more than', resp.content)

        self.rating['rating']['rating'] = settings.RATING_MIN - 1
        resp = self.update_article_rating()

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b'Rating cannot be less than', resp.content)

    def test_posting_to_existing_rating_updates_it(self):
        """Attempt to create an existing rating updates it instead"""
        resp = self.create_article_rating()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn(b'rating', resp.content)
        self.assertIn(b'4', resp.content)

        self.rating['rating']['rating'] = 5
        resp = self.create_article_rating()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn(b'rating', resp.content)
        self.assertIn(b'5', resp.content)
        
    def test_user_can_delete_an_article_rating(self):
        """A user can delete their own rating on an article"""
        self.create_article_rating()
        resp = self.client.delete(self.article_rating_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b'Successfully deleted rating', resp.content)

        # Getting a deleted rating returns the default rating only
        resp = self.client.get(self.article_rating_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotIn(b'\'rating\'', resp.content)
