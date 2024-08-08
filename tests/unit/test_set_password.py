import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.set_password import app
from unittest import TestCase

EVENT = {
    'body': json.dumps({
        'username': 'Gislane',
        'password': 'p?jl1#&HutH}',
        'new_password': '20213Tn105!'
    })
}


class Test(TestCase):
    def test_lambda_handler(self):
        response = app.lambda_handler(EVENT, None)

        body = json.loads(response['body'])
        expected_keys = ['id_token', 'access_token', 'refresh_token', 'username']

        for key in expected_keys:
            self.assertIn(key, body)

    def test_password_not_in_body(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'new_password': 'NewPass123!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Password is required"')

    def test_password_is_none(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': None,
                'new_password': 'NewPass123!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Password is required"')

    def test_password_is_not_str(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': 123,
                'new_password': 'NewPass123!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Password must be a string"')

    def test_username_not_in_body(self):
        event = {
            'body': json.dumps({
                'password': 'Password123!',
                'new_password': 'NewPass123!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Username is required"')

    def test_username_is_none(self):
        event = {
            'body': json.dumps({
                'username': None,
                'password': 'Password123!',
                'new_password': 'NewPass123!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Username is required"')

    def test_username_is_not_str(self):
        event = {
            'body': json.dumps({
                'username': 123,
                'password': 'Password123!',
                'new_password': 'NewPass123!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Username must be a string"')

    def test_new_password_not_in_body(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': 'Password123!'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"New password is required"')

    def test_new_password_is_none(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': 'Password123!',
                'new_password': None
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"New password is required"')

    def test_new_password_is_not_str(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': 'Password123!',
                'new_password': 123
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"New password must be a string"')

    def test_new_password_invalid_format(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'password': 'Password123!',
                'new_password': 'short'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'],
                         '"New password must contain at least 8 characters, one uppercase, one lowercase, one number and one special character"')

    @patch('modules.users.set_password.app.set_password')
    def test_exception_set_password(self, mock_set_password):

        mock_set_password.side_effect = Exception('Error')

        response = app.lambda_handler(EVENT, None)

        self.assertEqual(response['body'], '"Error"')


if __name__ == '__main__':
    unittest.main()