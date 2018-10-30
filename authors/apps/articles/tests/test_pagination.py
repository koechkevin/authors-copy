from .base_tests import BaseTest
from rest_framework.reverse import reverse as API_Reverse

class PagiationTest(BaseTest):
    def create_many_articles(self):
        token = self.create_and_login_user()
        for i in range(11):
            self.create_article(token=token)

    def test_articles_ar_paginated(self):
        '''See if  the return of get articles has count, next and previous articles'''
        url = API_Reverse('articles:articles')
        response = self.client.get(url)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("count", response.data)
    
    def test_more_than_ten_articles_are_paginated(self):
        self.create_many_articles()
        response=self.client.get(self.url)
        self.assertNotEqual(None, response.data["next"])
        self.assertEqual(11, response.data["count"])

    def test_next(self):
        self.create_many_articles()
        response=self.client.get(self.url)
        next_link = response.data["next"]
        response2 = self.client.get(next_link)
        self.assertEqual(None, response2.data["next"])
        #check that the previous link is there
        self.assertNotEqual(None, response2.data["previous"])
        #check only one result for next page
        self.assertEqual(1, len(response2.data["results"]))

    def test_prev(self):
        self.create_many_articles()
        response=self.client.get(self.url)
        next_link = response.data["next"]
        response = self.client.get(next_link)
        previous_link = response.data["previous"]
        response2 = self.client.get(previous_link)
        self.assertEqual(None, response2.data["previous"])
        #check that the next link is there
        self.assertNotEqual(None, response2.data["next"])
        #check only ten results for previous page
        self.assertEqual(10, len(response2.data["results"]))
