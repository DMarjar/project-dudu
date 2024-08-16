import unittest
from unittest.mock import patch, MagicMock
import json

from botocore.exceptions import ClientError, NoCredentialsError

from modules.profile.update_profile.app import lambda_handler, validate_body, get_secret
from modules.profile.update_profile.common.httpStatusCodeError import HttpStatusCodeError


class TestLambdaHandler(unittest.TestCase):

    @patch('modules.profile.update_profile.app.get_db_connection')
    @patch('modules.profile.update_profile.app.get_secret')
    @patch('modules.profile.update_profile.app.update_cognito_user')
    @patch('modules.profile.update_profile.app.update_user_db')
    def test_lambda_handler_success(self, mock_update_user_db, mock_update_cognito_user, mock_get_secret,
                                    mock_get_db_connection):
        # Mock methods
        mock_get_secret.return_value = {'USER_POOL_ID': 'fake_user_pool_id'}
        mock_update_cognito_user.return_value = None
        mock_update_user_db.return_value = None

        event = {
            'body': json.dumps({
                'sub': 'fake_sub',
                'id_user': 'fake_id_user',
                'email': 'test@example.com',
                'gender': 'M'
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), "User updated successfully")

    def test_validate_body_missing_gender(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': 'test@example.com'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_gender_with_extra_spaces(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': 'test@example.com',
            'gender': ' M '  # Gender with extra spaces
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_gender_empty_string(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': 'test@example.com',
            'gender': ''  # Gender as empty string
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    @patch('modules.profile.update_profile.app.get_db_connection')
    @patch('modules.profile.update_profile.app.get_secret')
    def test_lambda_handler_http_status_code_error(self, mock_get_secret, mock_get_db_connection):
        # Configuración de los mocks
        mock_get_secret.return_value = {'USER_POOL_ID': 'fake_user_pool_id'}
        # Evento con email inválido
        event = {
            'body': json.dumps({
                'sub': 'fake_sub',
                'id_user': 'fake_id_user',
                'email': 'invalid-email',
                'gender': 'M'
            })
        }

        # Ejecutar lambda_handler y verificar que se lance HttpStatusCodeError
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("Invalid email format", json.loads(response['body'])['message'])
    def test_validate_body_missing_email(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_invalid_email(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': 'invalid-email',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_missing_email(self):
        body = {
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_invalid_gender(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': 'test@example.com',
            'gender': 'X'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    @patch('modules.profile.update_profile.app.boto3.session.Session')
    def test_get_secret_success(self, mock_session):
        mock_secret = {'USER_POOL_ID': 'fake_user_pool_id'}
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.return_value = {'SecretString': json.dumps(mock_secret)}

        secret = get_secret()
        self.assertEqual(secret['USER_POOL_ID'], 'fake_user_pool_id')

    @patch('modules.profile.update_profile.app.boto3.session.Session')
    def test_get_secret_client_error(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Secret not found"}},
            "GetSecretValue"
        )

        with self.assertRaises(Exception) as context:
            get_secret()
        self.assertTrue("An error occurred" in str(context.exception))

    @patch('modules.profile.update_profile.app.boto3.session.Session')
    def test_get_secret_no_credentials_error(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.side_effect = NoCredentialsError()

        with self.assertRaises(HttpStatusCodeError):
            get_secret()
    @patch('modules.profile.update_profile.app.get_db_connection')
    @patch('modules.profile.update_profile.app.get_secret')
    @patch('modules.profile.update_profile.app.update_cognito_user')
    @patch('modules.profile.update_profile.app.update_user_db')
    def test_lambda_handler_client_error(self, mock_update_user_db, mock_update_cognito_user, mock_get_secret,
                                         mock_get_db_connection):
        mock_get_secret.return_value = {'USER_POOL_ID': 'fake_user_pool_id'}
        mock_update_cognito_user.side_effect = ClientError(
            {"Error": {"Code": "ClientError", "Message": "Client error"}},
            "AdminUpdateUserAttributes"
        )

        event = {
            'body': json.dumps({
                'sub': 'fake_sub',
                'id_user': 'fake_id_user',
                'email': 'test@example.com',
                'gender': 'M'
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("AWS Client Error", json.loads(response['body'])['message'])
    @patch('modules.profile.update_profile.app.get_db_connection')
    @patch('modules.profile.update_profile.app.get_secret')
    @patch('modules.profile.update_profile.app.update_cognito_user')
    @patch('modules.profile.update_profile.app.update_user_db')
    def test_lambda_handler_no_credentials_error(self, mock_update_user_db, mock_update_cognito_user,
                                                  mock_get_secret, mock_get_db_connection):
        mock_get_secret.side_effect = NoCredentialsError()

        event = {
            'body': json.dumps({
                'sub': 'fake_sub',
                'id_user': 'fake_id_user',
                'email': 'test@example.com',
                'gender': 'M'
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("Credentials Error", json.loads(response['body'])['message'])

    @patch('modules.profile.update_profile.app.get_db_connection')
    @patch('modules.profile.update_profile.app.get_secret')
    @patch('modules.profile.update_profile.app.update_cognito_user')
    @patch('modules.profile.update_profile.app.update_user_db')
    def test_lambda_handler_unexpected_error(self, mock_update_user_db, mock_update_cognito_user, mock_get_secret,
                                             mock_get_db_connection):
        mock_get_secret.return_value = {'USER_POOL_ID': 'fake_user_pool_id'}
        mock_update_cognito_user.side_effect = Exception("Unexpected error")

        event = {
            'body': json.dumps({
                'sub': 'fake_sub',
                'id_user': 'fake_id_user',
                'email': 'test@example.com',
                'gender': 'M'
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("An unexpected error occurred", json.loads(response['body'])['message'])

    def test_validate_body_sub_none(self):
        body = {
            'sub': None,
            'id_user': 'fake_id_user',
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_sub_not_string(self):
        body = {
            'sub': 123,
            'id_user': 'fake_id_user',
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_id_user_none(self):
        body = {
            'sub': 'fake_sub',
            'id_user': None,
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_id_user_not_string(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 123,
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_email_none(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': None,
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_email_not_string(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': 123,
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_gender_none(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': 'test@example.com',
            'gender': None
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_gender_invalid(self):
        body = {
            'sub': 'fake_sub',
            'id_user': 'fake_id_user',
            'email': 'test@example.com',
            'gender': 'X'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_id_user_missing(self):
        body = {
            'sub': 'fake_sub',
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)
    def test_validate_body_sub_empty(self):
        body = {
            'sub': '',
            'id_user': 'fake_id_user',
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "sub is required and must be a non-empty string")

    def test_validate_body_id_user_empty(self):
        body = {
            'sub': 'fake_sub',
            'id_user': '',
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        # Verifica el código de estado y el mensaje
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "id_user is required and must be a non-empty string")

if __name__ == '__main__':
    unittest.main()
