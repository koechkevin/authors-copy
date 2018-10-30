from rest_framework import status
import json

from authors.apps.articles.tests.base_tests import BaseTest, API_Reverse


class TagsTest(BaseTest):

    def setUp(self):
        """This method sets up tests for tags"""
        super().setUp()
        self.token = self.create_and_login_user()

    def test_user_can_create_article_with_tags(self):
        """This method tests if a user can create tags"""
        response = self.client.post(self.url, self.article, format='json', HTTP_AUTHORIZATION=self.token)
        self.assertIn('tags', json.dumps(response.data))
        self.assertIn('test', json.dumps(response.data))

    def test_user_can_create_article_without_tag(self):
        """This method test is a user can create an article without tag"""
        response = self.client.post(self.url, self.article, format='json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tags', json.dumps(response.data))

    def test_user_can_get_article_with_tags(self):
        """This method tests if a user can get an article with tags"""
        url = self.single_article_details()
        response = self.client.get(url, format='json')
        self.assertIn('tags', json.dumps(response.data))
        self.assertIn('test', json.dumps(response.data))

    def test_user_can_get_all_tags(self):
        """This method tests if a user can get all tags"""
        self.create_article()
        url = API_Reverse('tags:tags')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('test', json.dumps(response.data))
        self.assertIn('tags', json.dumps(response.data))

    def test_unauthorized_users_cannot_create_tags(self):
        """This method tests if unauthorized users can create tags"""
        url = API_Reverse('articles:articles')
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.post(url, data=self.article, format='json')
        self.assertIn('Authentication credentials were not provided', json.dumps(response.data))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tags_are_created_as_slugs(self):
        self.article['article']['tags'].extend(["NEW TAG"])
        response = self.client.post(self.url, self.article, format='json', HTTP_AUTHORIZATION=self.token)
        self.assertIn('new-tag', json.dumps(response.data))

    def test_user_cannot_post_special_characters_on_tags(self):
        self.article['article']['tags'].extend(["NEW TAG WITH Characters #$%"])
        response = self.client.post(self.url, self.article, format='json', HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Tag cannot have special characters', json.dumps(response.data))
        self.assertIn('error', json.dumps(response.data))
