import json
from modules.users.set_password import app
from unittest import TestCase

EVENT = {
    'body': json.dumps({
        'username': 'Atoferatofe',
        'password': 'wivPv}u8ktJ_',
        'new_password': '20213Tn105!'
    })
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))