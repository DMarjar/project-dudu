import json
from modules.users.login import app
from unittest import TestCase

EVENT = {
    'pathParameters': {
        'id_user': '41bb3510-c0a1-7093-8adf-af851d916edd'
    },
    'body': {
      'username': 'new_username',
      'email': 'new_email@example.com',
      'gender': 'male'
    }
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))
