import json
from modules.users.login import app
from unittest import TestCase

EVENT = {
    'body': json.dumps({
        'username': 'Merlynn',
        'password': 'c7e2MW@X'
    })
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))
