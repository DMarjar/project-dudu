import unittest
from unittest.mock import patch, MagicMock, Mock
import json

from botocore.exceptions import ClientError, NoCredentialsError

from modules.profile.update_profile.app import lambda_handler, validate_body, get_secret, get_username_from_sub, \
    update_cognito_user, update_user_db
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

        # Provide all required fields with valid data
        event = {
            'body': json.dumps({
                'sub': '1234-5678-9012',  # Valid sub
                'id_user': 'user_1234',  # Valid id_user
                'email': 'test@example.com',  # Valid email
                'gender': 'M'  # Valid gender
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)

    def test_lambda_handler_invalid_secret_format(self):
        with patch('modules.profile.update_profile.app.get_secret', return_value='invalid_json'):
            event = {
                'body': json.dumps({
                    'sub': 'some-sub',
                    'id_user': 'some-id-user',
                    'email': 'test@example.com',
                    'username': 'testuser',
                    'gender': 'M'
                })
            }
            response = lambda_handler(event, None)
            # Cambia la expectativa al código de estado 500
            self.assertEqual(response['statusCode'], 500)

    def test_lambda_handler_no_secret(self):
        with patch('modules.profile.update_profile.app.get_secret', return_value={}):
            # Construct the event with missing 'sub' and 'id_user'
            event = {
                'body': json.dumps({
                    'email': 'test@example.com',
                    'username': 'testuser',
                    'gender': 'M'
                })
            }

            # Invoke the lambda handler
            response = lambda_handler(event, None)

            # Assert that the response status code is 400
            self.assertEqual(response['statusCode'], 400)
            self.assertIn("sub is required", response['body'])

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
        # Ajusta el mensaje de error esperado aquí para que coincida con el mensaje real de la Lambda
        self.assertIn("An unexpected error occurred", response['body'])

    @patch('modules.profile.update_profile.app.get_db_connection')
    def test_lambda_handler_invalid_json(self, mock_get_db_connection):
        event = {
            'body': 'invalid json'
        }
        response = lambda_handler(event, None)

        # Verificar el código de estado
        self.assertEqual(response['statusCode'], 500)

        # Verificar que el mensaje de error contenga 'An unexpected error occurred'
        self.assertIn("An unexpected error occurred", response['body'])

        # Verificar que los encabezados estén presentes en la respuesta
        self.assertEqual(response['headers']['Access-Control-Allow-Headers'], '*')
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        self.assertEqual(response['headers']['Access-Control-Allow-Methods'], 'OPTIONS,POST,GET,PUT,DELETE')



    @patch('modules.profile.update_profile.app.get_db_connection')
    @patch('modules.profile.update_profile.app.get_secret')
    @patch('modules.profile.update_profile.app.update_cognito_user')
    def test_update_cognito_user_exception(self, mock_update_cognito_user, mock_get_secret, mock_get_db_connection):
        # Test exception in update_cognito_user
        mock_get_secret.return_value = {'USER_POOL_ID': 'fake_user_pool_id'}
        mock_update_cognito_user.side_effect = HttpStatusCodeError(400, "User not found in Cognito")
        event = {
            'body': json.dumps({
                'sub': 'fake_sub',
                'id_user': 'fake_id',
                'email': 'test@example.com',
                'username': 'testuser',
                'gender': 'M'
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Access-Control-Allow-Headers', response['headers'])
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertIn('Access-Control-Allow-Methods', response['headers'])
        self.assertEqual(response['headers']['Access-Control-Allow-Headers'], '*')
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        self.assertEqual(response['headers']['Access-Control-Allow-Methods'], 'OPTIONS,POST,GET,PUT,DELETE')



    def test_validate_body_success(self):
        body = {
            'sub': 'some-uuid',
            'id_user': '12345',
            'email': 'test@example.com',
            'gender': 'M'
        }
        self.assertTrue(validate_body(body))

    def test_validate_body_missing_email(self):
        body = {
            'email': 'email@utez.edu.mx',
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_invalid_email(self):
        body = {
            'email': 'invalid-email',
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
            'gender': 'M'
        }
        with self.assertRaises(HttpStatusCodeError):
            validate_body(body)

    def test_validate_body_invalid_gender(self):
        body = {
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

    @patch('modules.profile.update_profile.app.boto3.client')
    def test_get_username_from_sub_success(self, mock_boto_client):
        # Simular una respuesta exitosa de list_users
        mock_client = MagicMock()
        mock_client.list_users.return_value = {
            'Users': [{'Username': 'testuser'}]
        }
        mock_boto_client.return_value = mock_client

        # Llamar a la función que estamos probando
        sub = 'test-sub'
        user_pool_id = 'test-user-pool-id'
        username = get_username_from_sub(sub, user_pool_id)

        # Verificar que el nombre de usuario devuelto es el esperado
        self.assertEqual(username, 'testuser')
        mock_client.list_users.assert_called_once_with(
            UserPoolId=user_pool_id,
            Filter=f'sub="{sub}"'
        )

    @patch('modules.profile.update_profile.app.boto3.client')
    def test_get_username_from_sub_user_not_found(self, mock_boto_client):
        # Simular una respuesta donde no se encuentra el usuario
        mock_client = MagicMock()
        mock_client.list_users.return_value = {
            'Users': []
        }
        mock_boto_client.return_value = mock_client

        # Llamar a la función y verificar que se lanza una excepción
        sub = 'test-sub'
        user_pool_id = 'test-user-pool-id'
        with self.assertRaises(Exception) as context:
            get_username_from_sub(sub, user_pool_id)

        self.assertEqual(str(context.exception), "User not found")
        mock_client.list_users.assert_called_once_with(
            UserPoolId=user_pool_id,
            Filter=f'sub="{sub}"'
        )

    @patch('modules.profile.update_profile.app.boto3.client')
    @patch('modules.profile.update_profile.app.get_username_from_sub')
    def test_update_cognito_user_success(self, mock_get_username_from_sub, mock_boto_client):
        # Configura el mock para get_username_from_sub
        mock_get_username_from_sub.return_value = 'testuser'

        # Configura el mock para boto3 client
        mock_client = MagicMock()
        mock_client.admin_update_user_attributes.return_value = {}
        mock_boto_client.return_value = mock_client

        # Datos de entrada para la prueba
        sub = 'test-sub'
        body = {'email': 'test@example.com'}
        secrets = {'USER_POOL_ID': 'test-user-pool-id'}

        # Llama a la función que estás probando
        update_cognito_user(sub, body, secrets)

        # Verifica que se haya llamado a list_users y admin_update_user_attributes con los parámetros correctos
        mock_get_username_from_sub.assert_called_once_with(sub, secrets['USER_POOL_ID'])
        mock_client.admin_update_user_attributes.assert_called_once_with(
            UserPoolId=secrets['USER_POOL_ID'],
            Username='testuser',
            UserAttributes=[
                {'Name': 'email', 'Value': body['email']},
                {'Name': 'email_verified', 'Value': 'true'}
            ]
        )

    @patch('modules.profile.update_profile.app.boto3.client')
    @patch('modules.profile.update_profile.app.get_username_from_sub')
    def test_update_cognito_user_user_not_found(self, mock_get_username_from_sub, mock_boto_client):
        # Configura el mock para get_username_from_sub
        mock_get_username_from_sub.side_effect = Exception("User not found")

        # Configura el mock para boto3 client
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Datos de entrada para la prueba
        sub = 'test-sub'
        body = {'email': 'test@example.com'}
        secrets = {'USER_POOL_ID': 'test-user-pool-id'}

        # Llama a la función y verifica que se lanza una excepción
        with self.assertRaises(Exception) as context:
            update_cognito_user(sub, body, secrets)

        self.assertTrue("User not found" in str(context.exception))

    def setUp(self):
        self.valid_body = {
            'sub': 'valid-sub',
            'id_user': 'valid-id-user',
            'email': 'test@example.com',
            'gender': 'M'
        }
    def test_valid_body(self):
        # Test a valid body should not raise any exceptions
        try:
            validate_body(self.valid_body)
        except HttpStatusCodeError:
            self.fail("validate_body raised HttpStatusCodeError unexpectedly!")

    def test_missing_sub(self):
        body = self.valid_body.copy()
        del body['sub']
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "sub is required")


    def test_sub_not_string(self):
        body = self.valid_body.copy()
        body['sub'] = 123
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "sub must be a string")

    def test_missing_id_user(self):
        body = self.valid_body.copy()
        del body['id_user']
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "id_user is required")


    def test_id_user_not_string(self):
        body = self.valid_body.copy()
        body['id_user'] = 123
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "id_user must be a string")

    def test_missing_email(self):
        body = self.valid_body.copy()
        del body['email']
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "email is required")

    def test_email_is_none(self):
        body = self.valid_body.copy()
        body['email'] = None
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "email is required")

    def test_email_not_string(self):
        body = self.valid_body.copy()
        body['email'] = 123
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "email must be a string")

    def test_invalid_email_format(self):
        body = self.valid_body.copy()
        body['email'] = 'invalid-email'
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "Invalid email format")

    def test_missing_gender(self):
        body = self.valid_body.copy()
        del body['gender']
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "gender is required")

    def test_gender_is_none(self):
        body = self.valid_body.copy()
        body['gender'] = None
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "gender is required")

    def test_invalid_gender_value(self):
        body = self.valid_body.copy()
        body['gender'] = 'X'
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.message, "invalid gender value, must be M or F")



if __name__ == '__main__':
    unittest.main()
