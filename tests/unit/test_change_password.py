import json
import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from modules.users.change_password.app import lambda_handler


class FakeSecretsManagerClient:
    def get_secret_value(self, SecretId):
        if SecretId == "secret-id":
            return {
                'SecretString': json.dumps({'SECRET_CLIENT': 'fake_secret'})
            }
        else:
            raise ClientError(
                {"Error": {"Code": "ResourceNotFoundException"}},
                "get_secret_value"
            )


class FakeSession:
    def client(self, service_name, region_name):
        if service_name == 'secretsmanager' and region_name == 'us-east-1':
            return FakeSecretsManagerClient()
        else:
            raise ValueError("Unsupported service or region")


class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock()
        self.patcher_boto = patch('boto3.client', return_value=self.mock_client)
        self.patcher_get_secret = patch('modules.users.change_password.common.common_functions.get_secret')
        self.patcher_get_secret_hash = patch('modules.users.change_password.common.common_functions.get_secret_hash')

        self.mock_boto = self.patcher_boto.start()
        self.mock_get_secret = self.patcher_get_secret.start()
        self.mock_get_secret_hash = self.patcher_get_secret_hash.start()

        self.mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        self.mock_get_secret_hash.return_value = 'fake_secret_hash'

    def tearDown(self):
        self.patcher_boto.stop()
        self.patcher_get_secret.stop()
        self.patcher_get_secret_hash.stop()

    def test_successful_password_reset(self):
        self.mock_client.confirm_forgot_password.return_value = {}

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
        self.mock_client.confirm_forgot_password.side_effect = ClientError(
            {'Error': {'Code': 'CodeMismatchException', 'Message': 'The code passed is incorrect.'}},
            'ConfirmForgotPassword'
        )

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
        self.mock_client.confirm_forgot_password.side_effect = ClientError(
            {'Error': {'Code': 'ExpiredCodeException'}}, 'ConfirmForgotPassword'
        )

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
        self.mock_client.confirm_forgot_password.side_effect = ClientError(
            {'Error': {'Code': 'InvalidPasswordException'}}, 'ConfirmForgotPassword'
        )

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
        self.mock_client.confirm_forgot_password.side_effect = ClientError(
            {'Error': {'Code': 'UserNotFoundException'}}, 'ConfirmForgotPassword'
        )

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
        self.mock_client.confirm_forgot_password.side_effect = Exception('Some generic error')

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
    unittest.main()
