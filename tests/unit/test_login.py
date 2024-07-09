import json
from modules.users.login import app
from unittest import TestCase

EVENT = {
    'body': json.dumps({
        'username': 'Atoferatofe',
        'password': '20213Tn105!'
    })
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))
