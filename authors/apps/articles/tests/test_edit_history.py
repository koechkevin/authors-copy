from authors.apps.articles.tests.base_tests import BaseTest
import json

class TestEditHistory(BaseTest):
    def test_can_view_one_history(self):
        """#create comment, update and check if history field has content"""
        id, slug = self.create_comment()
        response_body = json.loads(self.update_comment(id, slug, 'new comment').content)
        self.assertEqual(len(response_body['history']), 1)
        self.assertEqual(response_body['history'][0]['body'], 'This is a test comment body.')
        self.assertEqual(response_body['body'], 'new comment')

    def test_user_views_successive_edits(self):
        """# all edits are returned"""
        id, slug = self.create_comment()
        self.update_comment(id, slug, 'first edit')
        self.update_comment(id, slug, 'second edit')
        response_body = json.loads(self.update_comment(id, slug, 'third edit').content)
        self.assertEqual(response_body['body'], 'third edit')
        self.assertEqual(len(response_body['history']), 3)
        self.assertEqual(response_body['history'][2]['body'],'second edit')

    def test_user_cannot_update_with_blank(self):
        id, slug = self.create_comment()
        response = self.update_comment(id, slug, '').content
        response_body = json.loads(response)
        error_message = response_body['errors']['body']
        self.assertEqual(error_message, ['This field may not be blank.'])

    def test_edit_history_sorted(self):
        """test that the edit history is sorted per the updated time"""
        id, slug = self.create_comment()
        self.update_comment(id, slug, 'first edit')
        self.update_comment(id, slug, 'second edit')
        response_body = json.loads(self.update_comment(id, slug, 'final edit').content)
        initial_comment = response_body['history'][0]['body']
        first_edit = response_body['history'][1]['body']
        second_edit = response_body['history'][2]['body']
        self.assertEqual(initial_comment, 'This is a test comment body.')
        self.assertEqual(first_edit, 'first edit')
        self.assertEqual(second_edit, 'second edit')

    def test_update_with_same_comment(self):
        """There should be no history provided if same comment is provided for update"""
        id, slug = self.create_comment()
        response_body = json.loads(self.update_comment(id, slug, 'This is a test comment body.').content)
        self.assertEqual(len(response_body['history']), 0)
