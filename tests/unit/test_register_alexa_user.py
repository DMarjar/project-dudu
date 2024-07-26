import json
from modules.users.register_alexa_user import app
from unittest import TestCase
import pytest

EVENT = {
    'body': json.dumps({
        'id_user': 'asdfasd',
        'username': 'Gislane'
    })
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))