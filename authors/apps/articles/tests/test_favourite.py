import json
from rest_framework.reverse import reverse
from rest_framework import status

from authors.apps.articles.tests.base_tests import BaseTest

class Favourite_tests(BaseTest):
    def test_authenticated_user_can_favourite(self):
        slug = self.create_article()
        url = reverse('articles:favourite', {slug:"slug"})
        response = self.client.post(url,format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_favourite(self):
        slug = self.create_article
        self.client.credentials(HTTP_AUTHORIZATION="")
        url = reverse('articles:favourite', {slug:"slug"})
        response = self.client.post(url,format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_cannot_favourite_twice(self):
        slug = self.create_article()
        url = reverse('articles:favourite', kwargs={"slug":slug})
        self.client.post(url, format='json')
        response = self.client.post(url, format='json')
        self.assertIn('You have already favourited this article', json.dumps(response.data))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_favourite_a_non_existing_article(self):
        self.create_and_login_user()
        slug="random_slug"
        url = reverse('articles:favourite', kwargs={"slug":slug})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_unfavourite(self):
        slug = self.create_article()
        url = reverse('articles:favourite', kwargs={"slug":slug})
        self.client.post(url, format='json')
        response = self.client.delete(url, format='json')
        self.assertIn('unfavourited', json.dumps(response.data))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_unfavourite(self):
        slug = self.create_article()
        url = reverse('articles:favourite', kwargs={"slug":slug})
        self.client.post(url, format='json')
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_unfavourite_twice(self):
        """Test a user cannot unfavourite an article they have already unfavourited"""
        slug = self.create_article()
        url = reverse('articles:favourite', kwargs={"slug":slug})
        response = self.client.post(url, format='json')
        response2 = self.client.delete(url, format='json')
        response3= self.client.delete(url, format='json')
        self.assertEqual(response3.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_unfavourite_article_not_favourited(self):
        """Test that a user cannot unfavourite an article they had not favourited"""
        slug = self.create_article()
        url = reverse('articles:favourite', kwargs={"slug":slug})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_unfavourited_non_existend_article(self):
        """User should not be able to unlike an article that does not exist"""
        self.create_and_login_user()
        slug = "non-existand"
        url = reverse('articles:favourite', kwargs={"slug":slug})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
   
