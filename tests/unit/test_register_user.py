import json
from modules.users.register_user import app
from unittest import TestCase

EVENT = {
    'body': json.dumps({
        'email': 'emilioetorres99@gmail.com',
        'username': 'Merlynn',
        'gender': 'M'
    })
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))
