import unittest
import json
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from modules.users.change_password.app import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch('boto3.client')
    @patch('modules.users.change_password.common.common_functions.get_secret')
    @patch('modules.users.change_password.common.common_functions.get_secret_hash')
    def test_successful_password_reset(self, mock_get_secret_hash, mock_get_secret, mock_boto_client):
        mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        mock_get_secret_hash.return_value = 'fake_secret_hash'
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.confirm_forgot_password.return_value = {}
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

    @patch('boto3.client')
    @patch('modules.users.change_password.common.common_functions.get_secret')
    @patch('modules.users.change_password.common.common_functions.get_secret_hash')
    def test_code_mismatch_exception(self, mock_get_secret_hash, mock_get_secret, mock_boto_client):
        mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        mock_get_secret_hash.return_value = 'fake_secret_hash'
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Configura el mock para lanzar una excepción CodeMismatchException
        mock_client.confirm_forgot_password.side_effect = ClientError(
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

    @patch('boto3.client')
    @patch('modules.users.change_password.common.common_functions.get_secret')
    @patch('modules.users.change_password.common.common_functions.get_secret_hash')
    def test_password_mismatch(self, mock_get_secret_hash, mock_get_secret, mock_boto_client):
        mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        mock_get_secret_hash.return_value = 'fake_secret_hash'
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

    @patch('boto3.client')
    @patch('modules.users.change_password.common.common_functions.get_secret')
    @patch('modules.users.change_password.common.common_functions.get_secret_hash')
    def test_expired_code_exception(self, mock_get_secret_hash, mock_get_secret, mock_boto_client):
        mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        mock_get_secret_hash.return_value = 'fake_secret_hash'
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.confirm_forgot_password.side_effect = ClientError(
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

    @patch('boto3.client')
    @patch('modules.users.change_password.common.common_functions.get_secret')
    @patch('modules.users.change_password.common.common_functions.get_secret_hash')
    def test_invalid_password_exception(self, mock_get_secret_hash, mock_get_secret, mock_boto_client):
        mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        mock_get_secret_hash.return_value = 'fake_secret_hash'
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.confirm_forgot_password.side_effect = ClientError(
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

    @patch('boto3.client')
    @patch('modules.users.change_password.common.common_functions.get_secret')
    @patch('modules.users.change_password.common.common_functions.get_secret_hash')
    def test_user_not_found_exception(self, mock_get_secret_hash, mock_get_secret, mock_boto_client):
        mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        mock_get_secret_hash.return_value = 'fake_secret_hash'
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.confirm_forgot_password.side_effect = ClientError(
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

    @patch('boto3.client')
    @patch('modules.users.change_password.common.common_functions.get_secret')
    @patch('modules.users.change_password.common.common_functions.get_secret_hash')
    def test_generic_exception(self, mock_get_secret_hash, mock_get_secret, mock_boto_client):
        mock_get_secret.return_value = {'SECRET_CLIENT': 'fake_secret'}
        mock_get_secret_hash.return_value = 'fake_secret_hash'
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.confirm_forgot_password.side_effect = Exception('Some generic error')

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
