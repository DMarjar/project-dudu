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
                'email': 'test@example.com',
                'username': 'testuser',
                'gender': 'M'
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), "User updated successfully")



    def test_lambda_handler_invalid_secret_format(self):
        with patch('modules.profile.update_profile.app.get_secret', return_value='invalid_json'):
            event = {
                'body': json.dumps({
                    'email': 'test@example.com',
                    'username': 'testuser',
                    'gender': 'M'
                })
            }
            response = lambda_handler(event, None)
            self.assertEqual(response['statusCode'], 500)
            self.assertIn("An error occurred", response['body'])

    def test_lambda_handler_no_secret(self):
        with patch('modules.profile.update_profile.app.get_secret', return_value={}):
            event = {
                'body': json.dumps({
                    'email': 'test@example.com',
                    'username': 'testuser',
                    'gender': 'M'
                })
            }
            response = lambda_handler(event, None)
            self.assertEqual(response['statusCode'], 500)
            self.assertIn("An error occurred", response['body'])

    def test_validate_body_missing_gender(self):
        body = {
            'email': 'test@example.com',
            'username': 'testuser'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_gender_with_extra_spaces(self):
        body = {
            'email': 'test@example.com',
            'username': 'testuser',
            'gender': ' M '  # Gender with extra spaces
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_gender_empty_string(self):
        body = {
            'email': 'test@example.com',
            'username': 'testuser',
            'gender': ''  # Gender as empty string
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)



    @patch('modules.profile.update_profile.app.get_db_connection')
    def test_lambda_handler_missing_body(self, mock_get_db_connection):
        event = {}
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("An error occurred", response['body'])

    @patch('modules.profile.update_profile.app.get_db_connection')
    def test_lambda_handler_invalid_json(self, mock_get_db_connection):
        event = {
            'body': 'invalid json'
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("An error occurred", response['body'])

    @patch('modules.profile.update_profile.app.get_db_connection')
    @patch('modules.profile.update_profile.app.get_secret')
    def test_lambda_handler_http_status_code_error(self, mock_get_secret, mock_get_db_connection):
        # Configuración de los mocks
        mock_get_secret.return_value = {'USER_POOL_ID': 'fake_user_pool_id'}
        # Evento con email inválido
        event = {
            'body': json.dumps({
                'email': 'invalid-email',
                'username': 'testuser',
                'gender': 'M'
            })
        }

        # Ejecutar lambda_handler y verificar que se lance HttpStatusCodeError
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("Invalid email format", json.loads(response['body'])['message'])

    @patch('modules.profile.update_profile.app.get_db_connection')
    @patch('modules.profile.update_profile.app.get_secret')
    @patch('modules.profile.update_profile.app.update_cognito_user')
    def test_update_cognito_user_exception(self, mock_update_cognito_user, mock_get_secret, mock_get_db_connection):
        # Test exception in update_cognito_user
        mock_get_secret.return_value = {'USER_POOL_ID': 'fake_user_pool_id'}
        mock_update_cognito_user.side_effect = HttpStatusCodeError(404, "User not found in Cognito")
        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'username': 'testuser',
                'gender': 'M'
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 404)
        self.assertIn("User not found in Cognito", response['body'])

    @patch('modules.profile.update_profile.app.get_secret')
    @patch('modules.profile.update_profile.app.update_user_db')
    @patch('modules.profile.update_profile.app.get_db_connection')
    def test_update_user_db_exception(self, mock_get_db_connection, mock_update_user_db, mock_get_secret):
        # Test exception in update_user_db
        mock_get_db_connection.return_value = MagicMock()
        mock_update_user_db.side_effect = HttpStatusCodeError(500, "Error updating user in DB")
        mock_get_secret.return_value = {'USER_POOL_ID': 'fake_user_pool_id'}

        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'username': 'testuser',
                'gender': 'M'
            })
        }

        # Llama a lambda_handler y verifica la respuesta
        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])  # Decodifica el JSON del cuerpo de la respuesta
        self.assertEqual(response_body['message'],
                         "An error occurred: Unable to locate credentials")  # Verifica el mensaje exacto

    def test_validate_body_success(self):
        body = {
            'email': 'test@example.com',
            'username': 'testuser',
            'gender': 'M'
        }
        self.assertTrue(validate_body(body))

    def test_validate_body_missing_email(self):
        body = {
            'username': 'testuser',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_invalid_email(self):
        body = {
            'email': 'invalid-email',
            'username': 'testuser',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_missing_username(self):
        body = {
            'email': 'test@example.com',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_short_username(self):
        body = {
            'email': 'test@example.com',
            'username': 'ab',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_long_username(self):
        body = {
            'email': 'test@example.com',
            'username': 'a' * 21,
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_invalid_gender(self):
        body = {
            'email': 'test@example.com',
            'username': 'testuser',
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
        self.assertEqual(secret, mock_secret)

    @patch('modules.profile.update_profile.app.boto3.session.Session')
    def test_get_secret_client_error(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.side_effect = ClientError({'Error': {'Code': 'InvalidRequestException'}},
                                                               'GetSecretValue')

        with self.assertRaises(HttpStatusCodeError):
            get_secret()

    @patch('modules.profile.update_profile.app.boto3.session.Session')
    def test_get_secret_no_credentials_error(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.side_effect = NoCredentialsError()

        with self.assertRaises(HttpStatusCodeError):
            get_secret()



if __name__ == '__main__':
    unittest.main()
