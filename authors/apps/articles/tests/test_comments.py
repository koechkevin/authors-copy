from rest_framework import status
from authors.apps.articles.tests.base_tests import BaseTest, API_Reverse, APITestCase, APIClient

class CommentsTests(BaseTest):
    """
    Comments test cases
    """

    def create_comment(self):
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.client.post(url, self.comment, format='json')
        return response, url

    def test_can_create_comment(self):
        """
        Test if authenticated users can create comments
        """
        response, url  = self.create_comment()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_user_cannot_comment(self):
        """
        Test unauthenticated users cannot create comments
        """
        # use a valid user to create article
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.unauthorised_client.post(url, self.comment, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_users_can_view_comments(self):
        """
        Test users can view all comments
        """
        response, url = self.create_comment()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorised_users_can_view_comments(self):
        """
        Test any user can view somments
        """
        response, url = self.create_comment()
        response = self.unauthorised_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_view_single_comment(self):
        """
        Test users can view a single comment
        """
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.client.post(url, self.comment, format='json')
        id = response.data['id']
        url = API_Reverse('articles:comment-details', {slug: 'slug', id: 'id'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_thread_a_comment(self):
        """
        Test users can thread a comment
        """
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.client.post(url, self.comment, format='json')
        id = response.data['id']
        url = API_Reverse('articles:comment-details', {slug: 'slug', id: 'id'})
        response = self.client.post(url, data={'comment': {'body': 'child comment'}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_can_delete_comment(self):
        """
        Test authenticated users can delete their comments
        """
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.client.post(url, self.comment, format='json')
        id = response.data['id']
        url = API_Reverse('articles:comment-details', {slug: 'slug', id: 'id'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_delete_comment(self):
        """
        Test non-owners of comments cannot delete comments
        """
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.client.post(url, self.comment, format='json')
        id = response.data['id']
        url = API_Reverse('articles:comment-details', {slug: 'slug', id: 'id'})
        response = self.unauthorised_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_update_comment(self):
        """
        Test authenticated users can update their comments
        """
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.client.post(url, self.comment, format='json')
        id = response.data['id']
        url = API_Reverse('articles:comment-details', {slug: 'slug', id: 'id'})
        response = self.client.put(url, data={'comment': {'body': 'New comment'}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_update_comment(self):
        """
        Test non-owners of comments cannot update comments
        """
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.client.post(url, self.comment, format='json')
        id = response.data['id']
        url = API_Reverse('articles:comment-details', {slug: 'slug', id: 'id'})
        response = self.unauthorised_client.put(url, data={'comment': {'body': 'New comment'}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_comment_on_unavailable_article(self):
        """
        Test user cannot comment on an unavailable article
        """
        self.create_user()
        self.activate_user()
        token = self.login_user()
        self.client.credentials(HTTP_AUTHORIZATION=token)
        url = '/api/articles/slug/comments/'
        response = self.client.post(url, self.comment, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_get_comments_on_unavailable_article(self):
        """
        Test user cannot get comments from an unavailable article
        """
        self.create_user()
        url = '/api/articles/slug/comments/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_get_comment_on_unavailable_article(self):
        """
        Test user cannot get a comment from an unavailable article
        """
        self.create_user()
        url = '/api/articles/slug/comments/1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_cannot_delete_comments_on_unavailable_article(self):
        """
        Test user cannot delete comment on an unavailable article
        """
        self.create_user()
        self.activate_user()
        token = self.login_user()
        self.client.credentials(HTTP_AUTHORIZATION=token)
        url = '/api/articles/slug/comments/1/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_delete_unavailable_comment(self):
        """
        Test user cannot delete an unavailable comment
        """
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        url = API_Reverse('articles:comment-details', {slug: 'slug', 1: 'id'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_comment_on_unavailable_article(self):
        """
        Test user cannot update comment on an unavailable article
        """
        self.create_user()
        self.activate_user()
        token = self.login_user()
        self.client.credentials(HTTP_AUTHORIZATION=token)
        url = API_Reverse('articles:comment-details', {'slug': 'slug', 1: 'id'})
        response = self.client.put(url, data={'comment': {'body': 'New comment'}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_update_unavailable_comment(self):
        """
        Test user cannot update an unavailable comment
        """
        slug = self.create_article()
        url = API_Reverse('articles:comments', {slug: 'slug'})
        response = self.client.post(url, self.comment, format='json')
        url = API_Reverse('articles:comment-details', {slug: 'slug', 1: 'id'})
        response = self.client.put(url, data={'comment': {'body': 'New comment'}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)