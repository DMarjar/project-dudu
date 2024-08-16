import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.recover_password import app
from unittest import TestCase

EVENT = {'body': json.dumps({
    'username': '20213tn105@utez.edu.mx'
})}


class Test(TestCase):
    def test_lambda_handler(self):
        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'], '"Confirmation code sent successfully."')
