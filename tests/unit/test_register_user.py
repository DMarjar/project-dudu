import json
from modules.users.register_user import app
from unittest import TestCase

EVENT = {
    'body': json.dumps({
        'email': '20213tn105@utez.edu.mx',
        'username': 'Atoferatofe',
        'gender': 'M'
    })
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))
