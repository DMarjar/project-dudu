import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.set_password import app
from unittest import TestCase
import boto3

EVENT = {
    'body': json.dumps({
        'username': 'Gislane',
        'password': 'p?jl1#&HutH}',
        'new_password': '20213Tn105!'
    })
}

FAKE_SECRET = {'SecretString': json.dumps({
            'SECRET_CLIENT': 'client',
            'ID_CLIENT': 'id',
            'USER_POOL_ID': 'pool'
        })}


# To test_lambda_handler
class FakeSessionTestLambdaHandler:
    """
    FakeSession class to mock boto3 session
    """
    def __init__(self, *args, **kwargs):
        pass

    def client(self, *args, **kwargs):
        return FakeBoto3ClientTestLambdaHandler()
class FakeBoto3ClientTestLambdaHandler:
    def __init__(self, *args, **kwargs):
        pass

    def get_secret_value(self, *args, **kwargs):
        return FAKE_SECRET

    def admin_initiate_auth(self, *args, **kwargs):
        return {'ChallengeName': 'NEW_PASSWORD_REQUIRED', 'Session': 'session'}

    def respond_to_auth_challenge(self, *args, **kwargs):
        return MagicMock()

    def admin_update_user_attributes(self, *args, **kwargs):
        return MagicMock()

    def initiate_auth(self, *args, **kwargs):
        return {'AuthenticationResult': {
            'IdToken': 'id_token',
            'AccessToken': 'access_token',
            'RefreshToken': 'refresh_token'
        }}





class Test(TestCase):
    @patch('boto3.client')
    @patch('boto3.session.Session')
    def test_lambda_handler(self, mock_session, mock_client):
        mock_session.return_value = FakeSessionTestLambdaHandler()
        mock_client.return_value = FakeBoto3ClientTestLambdaHandler()

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
    @patch('boto3.session.Session')
    def test_exception_set_password(self, mock_session, mock_set_password):
        mock_session.return_value = FakeSessionTestLambdaHandler()
        mock_set_password.side_effect = Exception('Error')

        response = app.lambda_handler(EVENT, None)

        self.assertEqual(response['body'], '"Error"')


if __name__ == '__main__':
    unittest.main()