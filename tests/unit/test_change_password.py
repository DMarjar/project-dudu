import json
import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from modules.users.change_password.app import lambda_handler


class FakeSecretsManagerClient:
    def get_secret_value(self, SecretId):
        if SecretId == "users_pool/client_secret2":
            return {
                'SecretString': json.dumps({'SECRET_CLIENT': 'fake_secret'})
            }
        else:
            raise ClientError(
                {"Error": {"Code": "ResourceNotFoundException"}},
                "get_secret_value"
            )

    def confirm_forgot_password(self, **kwargs):
        """Simula el método confirm_forgot_password."""
        return {}


class FakeCognitoIdpClient:
    def confirm_forgot_password(self, **kwargs):
        """Simula el método confirm_forgot_password."""
        return {}


class FakeSession:
    def client(self, service_name, region_name=None):
        if service_name == 'secretsmanager' and region_name == 'us-east-2':
            return FakeSecretsManagerClient()
        else:
            raise ValueError("Unsupported service or region")


class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        self.patcher_boto_session = patch('boto3.session.Session', return_value=FakeSession())
        self.mock_boto_session = self.patcher_boto_session.start()

        # Preparar mocks para las funciones de recuperación de secretos
        self.patcher_get_secret = patch('modules.users.change_password.common.common_functions.get_secret')
        self.patcher_get_secret_hash = patch('modules.users.change_password.common.common_functions.get_secret_hash')

        self.mock_get_secret = self.patcher_get_secret.start()
        self.mock_get_secret_hash = self.patcher_get_secret_hash.start()

        self.mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        self.mock_get_secret_hash.return_value = 'fake_secret_hash'

    def tearDown(self):
        self.patcher_boto_session.stop()
        self.patcher_get_secret.stop()
        self.patcher_get_secret_hash.stop()

    def test_successful_password_reset(self):
        with patch('modules.users.change_password.app.boto3.client', return_value=FakeCognitoIdpClient()):
            event = {
                'body': json.dumps({
                    'username': 'testuser',
                    'confirmation_code': '123456',
                    'new_password': 'newpassword123',
                    'confirm_new_password': 'newpassword123'
                })
            }

            context = {}
            response = lambda_handler(event, context)
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), 'Password has been reset successfully.')

    def test_code_mismatch_exception(self):
        with patch('modules.users.change_password.app.boto3.client', return_value=FakeCognitoIdpClient()):
            # Simulamos la excepción CodeMismatchException en el cliente de Cognito
            with patch.object(FakeCognitoIdpClient, 'confirm_forgot_password', side_effect=ClientError(
                    {'Error': {'Code': 'CodeMismatchException', 'Message': 'The code passed is incorrect.'}},
                    'ConfirmForgotPassword'
            )):
                event = {
                    'body': json.dumps({
                        'username': 'testuser',
                        'confirmation_code': '123456',
                        'new_password': 'newpassword123',
                        'confirm_new_password': 'newpassword123'
                    })
                }

                context = {}
                response = lambda_handler(event, context)

                self.assertEqual(response['statusCode'], 400)
                self.assertEqual(json.loads(response['body']), 'Invalid confirmation code.')

    def test_password_mismatch(self):
        with patch('modules.users.change_password.app.boto3.client', return_value=FakeCognitoIdpClient()):
            event = {
                'body': json.dumps({
                    'username': 'testuser',
                    'confirmation_code': '123456',
                    'new_password': 'newpassword123',
                    'confirm_new_password': 'mismatchpassword'
                })
            }

            context = {}
            response = lambda_handler(event, context)

            self.assertEqual(response['statusCode'], 400)
            self.assertEqual(json.loads(response['body']), 'New password and confirmation password do not match.')

    def test_expired_code_exception(self):
        with patch('modules.users.change_password.app.boto3.client', return_value=FakeCognitoIdpClient()):
            # Simulamos la excepción ExpiredCodeException en el cliente de Cognito
            with patch.object(FakeCognitoIdpClient, 'confirm_forgot_password', side_effect=ClientError(
                    {'Error': {'Code': 'ExpiredCodeException', 'Message': 'The confirmation code has expired.'}},
                    'ConfirmForgotPassword'
            )):
                event = {
                    'body': json.dumps({
                        'username': 'testuser',
                        'confirmation_code': '123456',
                        'new_password': 'newpassword123',
                        'confirm_new_password': 'newpassword123'
                    })
                }

                context = {}
                response = lambda_handler(event, context)

                self.assertEqual(response['statusCode'], 400)
                self.assertEqual(json.loads(response['body']), 'Confirmation code has expired.')

    def test_invalid_password_exception(self):
        with patch('modules.users.change_password.app.boto3.client', return_value=FakeCognitoIdpClient()):
            # Simulamos la excepción InvalidPasswordException en el cliente de Cognito
            with patch.object(FakeCognitoIdpClient, 'confirm_forgot_password', side_effect=ClientError(
                    {'Error': {'Code': 'InvalidPasswordException', 'Message': 'The password provided is invalid.'}},
                    'ConfirmForgotPassword'
            )):
                event = {
                    'body': json.dumps({
                        'username': 'testuser',
                        'confirmation_code': '123456',
                        'new_password': 'newpassword123',
                        'confirm_new_password': 'newpassword123'
                    })
                }

                context = {}
                response = lambda_handler(event, context)

                self.assertEqual(response['statusCode'], 400)
                self.assertEqual(json.loads(response['body']), 'Invalid password.')

    def test_user_not_found_exception(self):
        with patch('modules.users.change_password.app.boto3.client', return_value=FakeCognitoIdpClient()):
            # Simulamos la excepción UserNotFoundException en el cliente de Cognito
            with patch.object(FakeCognitoIdpClient, 'confirm_forgot_password', side_effect=ClientError(
                    {'Error': {'Code': 'UserNotFoundException', 'Message': 'User does not exist.'}},
                    'ConfirmForgotPassword'
            )):
                event = {
                    'body': json.dumps({
                        'username': 'testuser',
                        'confirmation_code': '123456',
                        'new_password': 'newpassword123',
                        'confirm_new_password': 'newpassword123'
                    })
                }

                context = {}
                response = lambda_handler(event, context)

                self.assertEqual(response['statusCode'], 404)
                self.assertEqual(json.loads(response['body']), 'User not found.')

    def test_generic_exception(self):
        with patch('modules.users.change_password.app.boto3.client', return_value=FakeCognitoIdpClient()):
            # Simulamos una excepción genérica en el cliente de Cognito
            with patch.object(FakeCognitoIdpClient, 'confirm_forgot_password',
                              side_effect=Exception('Some generic error')):
                event = {
                    'body': json.dumps({
                        'username': 'testuser',
                        'confirmation_code': '123456',
                        'new_password': 'newpassword123',
                        'confirm_new_password': 'newpassword123'
                    })
                }

                context = {}
                response = lambda_handler(event, context)

                self.assertEqual(response['statusCode'], 500)
                self.assertEqual(json.loads(response['body']),
                                 'An error occurred while resetting the password: Some generic error')

    if __name__ == '__main__':
        unittest.main()  # pragma: no cover