import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.login import app

EVENT = {
    'body': json.dumps({
        'username': 'Gislane',
        'password': '20213Tn105!'
    })
}

EVENT_UPDATE_PASSWORD = {
    'body': json.dumps({
        'username': 'Atoferatofe',
        'password': 'zc/X6kjJiNsB'
    })
}


class Test(unittest.TestCase):
    def test_lambda_handler(self):
        response = app.lambda_handler(EVENT, None)

        body = json.loads(response['body'])
        expected_keys = ['id_token', 'access_token', 'refresh_token', 'username']

        for key in expected_keys:
            self.assertIn(key, body)

    def test_username_not_in_body(self):
        event = {
            'body': json.dumps({
                'password': '20213Tn105!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Username is required"')

    def test_username_is_empty(self):
        event = {
            'body': json.dumps({
                'username': '',
                'password': '20213Tn105!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Username is required"')

    def test_username_is_none(self):
        event = {
            'body': json.dumps({
                'username': None,
                'password': '20213Tn105!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Username is required"')

    def test_username_is_not_str(self):
        event = {
            'body': json.dumps({
                'username': 123,
                'password': '20213Tn105!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Username must be a string"')

    # Pruebas para las validaciones de 'password'
    def test_password_not_in_body(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Password is required"')

    def test_password_is_empty(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': ''
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Password is required"')

    def test_password_is_none(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': None
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Password is required"')

    def test_password_is_not_str(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': 123
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Password must be a string"')

    @patch('modules.users.login.app.boto3.client')
    def test_exception_client_initiate_auth(self, mock_client):
        mock_client.side_effect = Exception('An error occurred')

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['statusCode'], 401)
        self.assertEqual(response['body'], '"User or password incorrect"')

    def test_must_change_password(self):
        response = app.lambda_handler(EVENT_UPDATE_PASSWORD, None)
        self.assertEqual(response['body'], '"MUST CHANGE TEMPORARY PASSWORD"')

if __name__ == '__main__':
    unittest.main()