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

    def admin_get_user(self, *args, **kwargs):
        return {'UserStatus': 'CONFIRMED', 'UserAttributes': [{}, {'Name': 'email_verified', 'Value': 'true'}]}

    def initiate_auth(self, *args, **kwargs):
        return {'AuthenticationResult': {
            'IdToken': 'id_token',
            'AccessToken': 'access_token',
            'RefreshToken': 'refresh_token'
        }}


class FakeBoto3ClientTestLambdaHandlerMustChangePassword:
    def __init__(self, *args, **kwargs):
        pass

    def get_secret_value(self, *args, **kwargs):
        return FAKE_SECRET

    def admin_get_user(self, *args, **kwargs):
        return {'UserStatus': 'FORCE_CHANGE_PASSWORD', 'UserAttributes': [{}, {'Name': 'email_verified', 'Value': 'true'}]}


class Test(unittest.TestCase):
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
    @patch('boto3.session.Session')
    def test_exception_client_initiate_auth(self, mock_session, mock_client):
        mock_session.return_value = FakeSessionTestLambdaHandler()
        mock_client.side_effect = Exception('An error occurred')

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['statusCode'], 401)
        self.assertEqual(response['body'], '"User or password incorrect"')

    @patch('boto3.client')
    @patch('boto3.session.Session')
    def test_must_change_password(self, mock_session, mock_client):
        mock_session.return_value = FakeSessionTestLambdaHandler()
        mock_client.return_value = FakeBoto3ClientTestLambdaHandlerMustChangePassword()

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'], '"MUST CHANGE TEMPORARY PASSWORD"')


if __name__ == '__main__':
    unittest.main()