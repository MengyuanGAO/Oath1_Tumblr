import unittest
import SI507project5_code as projcode
import json
import os
from datetime import datetime


class Test_Tumblr_API(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        try:
            os.remove('cache_contents.json')
        except OSError:
            pass

        try:
            os.remove('creds.json')
        except OSError:
            pass

        self.blog_id = 'kldpxl'
        self.posts = projcode.get_result(self.blog_id)
        projcode.write_to_csv(self.blog_id, self.posts)
        self.contents_json_file = open('cache_contents.json', 'r', encoding='utf-8')
        self.creds_json_file = open('creds.json', 'r', encoding='utf-8')
        self.cache_diction = json.loads(self.contents_json_file.read())
        self.creds_diction = json.loads(self.creds_json_file.read())
        self.csv_file = open(self.blog_id + '.csv', 'r', encoding='utf-8')

    def test_cache_expire(self):
        cache_timestamp = datetime.strptime(self.creds_diction["TUMBLR"]["timestamp"], projcode.DATETIME_FORMAT)
        hasexpired = projcode.has_cache_expired(self.creds_diction["TUMBLR"]["timestamp"], self.creds_diction["TUMBLR"]["expire_in_days"])
        delta = datetime.now() - cache_timestamp
        self.assertEqual(delta.days > self.creds_diction["TUMBLR"]["expire_in_days"], hasexpired)

    def test_cache_posts_success(self):
        self.assertFalse(os.fstat(self.contents_json_file.fileno()).st_size == 0)
        self.assertIsInstance(self.cache_diction, dict)

    def test_cache_creds_success(self):
        self.assertFalse(os.fstat(self.creds_json_file.fileno()).st_size == 0)
        self.assertIsInstance(self.creds_diction, dict)

    def test_get_result_success(self):
        for post in self.posts:
            self.assertIsInstance(post, projcode.Post)
            self.assertIsInstance(post.title, str)
            self.assertIsInstance(post.note_count, int)
            self.assertIsInstance(post.summary, str)
            self.assertIsInstance(post.tags, list)
            self.assertIsInstance(post.date, str)
            self.assertIsInstance(post.url, str)

    def test_write_to_csv_success(self):
        self.assertFalse(os.fstat(self.csv_file.fileno()).st_size == 0)

    @classmethod
    def tearDownClass(self):
        self.contents_json_file.close()
        self.creds_json_file.close()
        self.csv_file.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
