import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.login import app

EVENT = {
    'body': json.dumps({
        'username': 'Atoferatofe',
        'password': '20213Tn105!'
    })
}


class Test(unittest.TestCase):
    def test_lambda_handler(self):
        response = app.lambda_handler(EVENT, None)

        print(response)
