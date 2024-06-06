from unittest import TestCase
from modules.get_all_missions.app import lambda_handler


class Test(TestCase):
    def test_lambda_handler(self):
        self.assertEqual(lambda_handler(None, None), {'statusCode': 200, 'body': '[]'})
