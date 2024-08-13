import unittest
from unittest.mock import patch, MagicMock
import json
from botocore.exceptions import ClientError, NoCredentialsError
from modules.profile.get_profile.app import lambda_handler, get_secret
from modules.profile.get_profile.common.httpStatusCodeError import HttpStatusCodeError


class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        # Setup any needed test data or mocks
        self.headers = {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }

    @patch('modules.profile.get_profile.app.get_db_connection')
    @patch('modules.profile.get_profile.app.validate_user')
    @patch('modules.profile.get_profile.app.get_profile')
    def test_lambda_handler_success(self, mock_get_profile, mock_validate_user, mock_get_db_connection):
        # Mock the database connection and cursor
        mock_get_db_connection.return_value = MagicMock()
        mock_validate_user.return_value = {'user_count': 1}
        mock_get_profile.return_value = {
            'id_user': 'valid_user',
            'level': 1,
            'current_xp': 50,
            'gender': 'M',
            'username': 'test_user',
            'xp_limit': 100,
            'id_reward': 1,
            'unlock_level': 1,
            'wizard_title': 'Wizard',
            'completed_missions': 5,
            'failed_missions': 2,
            'canceled_missions': 1
        }

        event = {
            'body': json.dumps({'id_user': 'valid_user'})
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertIn('profile', response_body)
        self.assertEqual(response_body['profile']['id_user'], 'valid_user')

    @patch('modules.profile.get_profile.app.get_db_connection')
    def test_lambda_handler_missing_body(self, mock_get_db_connection):
        # Test missing body in event
        event = {}
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("Bad request: Body is required", response['body'])

    @patch('modules.profile.get_profile.app.get_db_connection')
    def test_lambda_handler_missing_id_user(self, mock_get_db_connection):
        # Test missing id_user
        event = {
            'body': json.dumps({})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("Bad request: ID is required", response['body'])

    @patch('modules.profile.get_profile.app.get_db_connection')
    def test_lambda_handler_empty_id_user(self, mock_get_db_connection):
        # Test empty id_user
        event = {
            'body': json.dumps({'id_user': ''})  # Empty string
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)  # Changed to 400
        self.assertIn("Bad request: ID cannot be empty", response['body'])

    @patch('modules.profile.get_profile.app.get_db_connection')
    @patch('modules.profile.get_profile.app.validate_user')
    def test_lambda_handler_sql_exception(self, mock_validate_user, mock_get_db_connection):
        # Test SQL exception in validate_user
        mock_validate_user.side_effect = Exception("Database error")

        event = {
            'body': json.dumps({'id_user': 'valid_user'})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("An error occurred", response['body'])

    @patch('modules.profile.get_profile.app.get_db_connection')
    @patch('modules.profile.get_profile.app.get_profile')
    def test_lambda_handler_db_connection_error(self, mock_get_profile, mock_get_db_connection):
        # Test database connection error
        mock_get_db_connection.side_effect = Exception("Connection error")
        event = {
            'body': json.dumps({'id_user': 'valid_user'})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("An error occurred", response['body'])

    @patch('modules.profile.get_profile.app.get_db_connection')
    def test_lambda_handler_invalid_id_user(self, mock_get_db_connection):
        # Test invalid id_user
        event = {
            'body': json.dumps({'id_user': 12345})  # Invalid type
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)  # Changed to 400
        self.assertIn("Bad request: ID must be a string", response['body'])

    @patch('modules.profile.get_profile.app.get_db_connection')
    @patch('modules.profile.get_profile.app.validate_user')
    def test_lambda_handler_user_not_found(self, mock_validate_user, mock_get_db_connection):
        # Test user not found
        mock_validate_user.return_value = {'user_count': 0}

        event = {
            'body': json.dumps({'id_user': 'non_existing_user'})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 404)
        self.assertIn("User not found", response['body'])

    @patch('modules.profile.get_profile.app.get_db_connection')
    @patch('modules.profile.get_profile.app.validate_user')
    @patch('modules.profile.get_profile.app.get_profile')
    def test_lambda_handler_no_profile(self, mock_get_profile, mock_validate_user, mock_get_db_connection):
        # Test no profile found
        mock_validate_user.return_value = {'user_count': 1}
        mock_get_profile.return_value = None

        event = {
            'body': json.dumps({'id_user': 'valid_user'})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 404)
        self.assertIn("No profile information found", response['body'])

    @patch('modules.profile.get_profile.app.boto3.session.Session')
    def test_get_secret_success(self, mock_session):
        mock_secret = {'key': 'value'}
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.return_value = {'SecretString': json.dumps(mock_secret)}

        secret = get_secret()
        self.assertEqual(secret, mock_secret)

    @patch('modules.profile.get_profile.app.boto3.session.Session')
    def test_get_secret_client_error(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.side_effect = ClientError({'Error': {'Code': 'InvalidRequestException'}}, 'GetSecretValue')

        with self.assertRaises(HttpStatusCodeError):
            get_secret()

    @patch('modules.profile.get_profile.app.boto3.session.Session')
    def test_get_secret_no_credentials_error(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.side_effect = NoCredentialsError()

        with self.assertRaises(HttpStatusCodeError):
            get_secret()

    @patch('modules.profile.get_profile.app.get_db_connection')
    def test_lambda_handler_json_decode_error(self, mock_get_db_connection):
        # Test JSON decode error
        event = {
            'body': '{id_user: "valid_user"}'  # Invalid JSON
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("An error occurred", response['body'])

    @patch('modules.profile.get_profile.app.get_db_connection')
    def test_lambda_handler_db_connection_close(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_get_db_connection.return_value = mock_connection

        event = {
            'body': json.dumps({'id_user': 'valid_user'})
        }
        lambda_handler(event, None)
        self.assertTrue(mock_connection.close.called)

if __name__ == '__main__':
    unittest.main()
