import unittest
from unittest.mock import patch, MagicMock
import json
from botocore.exceptions import ClientError
from modules.users.change_password.app import lambda_handler
from modules.users.change_password.common.common_functions import get_secret


class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        self.client_patch = patch('boto3.client')
        self.mock_client = self.client_patch.start()

        self.get_secret_patch = patch('modules.users.change_password.common.common_functions.get_secret')
        self.mock_get_secret = self.get_secret_patch.start()

        self.get_secret_hash_patch = patch('modules.users.change_password.common.common_functions.get_secret_hash')
        self.mock_get_secret_hash = self.get_secret_hash_patch.start()

        self.mock_get_secret.return_value = {'SECRET_CLIENT': 'mock_secret_client'}
        self.mock_get_secret_hash.return_value = 'mock_secret_hash'

        self.mock_client_exceptions = MagicMock()
        self.mock_client.return_value.exceptions = self.mock_client_exceptions

        class CodeMismatchException(Exception):
            pass

        self.mock_client_exceptions.CodeMismatchException = CodeMismatchException

        class ExpiredCodeException(Exception):
            pass

        self.mock_client_exceptions.ExpiredCodeException = ExpiredCodeException

        class InvalidPasswordException(Exception):
            pass

        self.mock_client_exceptions.InvalidPasswordException = InvalidPasswordException

        class UserNotFoundException(Exception):
            pass

        self.mock_client_exceptions.UserNotFoundException = UserNotFoundException

    def tearDown(self):
        patch.stopall()

    def test_successful_password_reset(self):
        event = {
            'body': json.dumps({
                'username': 'test_user',
                'confirmation_code': '123456',
                'new_password': 'NewPassword123',
                'confirm_new_password': 'NewPassword123'
            })
        }
        context = {}

        self.mock_client().confirm_forgot_password.return_value = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Password has been reset successfully', response['body'])

    def test_password_mismatch(self):
        event = {
            'body': json.dumps({
                'username': 'test_user',
                'confirmation_code': '123456',
                'new_password': 'NewPassword123',
                'confirm_new_password': 'DifferentPassword123'
            })
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('New password and confirmation password do not match', response['body'])

    def test_code_mismatch_exception(self):
        event = {
            'body': json.dumps({
                'username': 'test_user',
                'confirmation_code': 'wrong_code',
                'new_password': 'NewPassword123',
                'confirm_new_password': 'NewPassword123'
            })
        }
        context = {}

        self.mock_client().confirm_forgot_password.side_effect = self.mock_client_exceptions.CodeMismatchException(
            {'Error': {'Code': 'CodeMismatchException'}}, 'confirm_forgot_password')

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Invalid confirmation code', response['body'])

    def test_expired_code_exception(self):
        event = {
            'body': json.dumps({
                'username': 'test_user',
                'confirmation_code': 'expired_code',
                'new_password': 'NewPassword123',
                'confirm_new_password': 'NewPassword123'
            })
        }
        context = {}

        self.mock_client().confirm_forgot_password.side_effect = self.mock_client_exceptions.ExpiredCodeException(
            {'Error': {'Code': 'ExpiredCodeException'}}, 'confirm_forgot_password')

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Confirmation code has expired', response['body'])

    def test_user_not_found_exception(self):
        event = {
            'body': json.dumps({
                'username': 'unknown_user',
                'confirmation_code': '123456',
                'new_password': 'NewPassword123',
                'confirm_new_password': 'NewPassword123'
            })
        }
        context = {}

        self.mock_client().confirm_forgot_password.side_effect = self.mock_client_exceptions.UserNotFoundException(
            {'Error': {'Code': 'UserNotFoundException'}}, 'confirm_forgot_password')

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('User not found', response['body'])

    def test_invalid_password_exception(self):
        event = {
            'body': json.dumps({
                'username': 'test_user',
                'confirmation_code': '123456',
                'new_password': 'weak',
                'confirm_new_password': 'weak'
            })
        }
        context = {}

        self.mock_client().confirm_forgot_password.side_effect = self.mock_client_exceptions.InvalidPasswordException(
            {'Error': {'Code': 'InvalidPasswordException'}}, 'confirm_forgot_password')

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Invalid password:', response['body'])

    @patch('boto3.session.Session.client')
    def test_get_secrets_client_error(self, mock_client):
        mock_client.return_value.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'get_secret_value')
        with self.assertRaises(ClientError):
            get_secret()

    def test_general_exception(self):
        event = {
            'body': json.dumps({
                'username': 'test_user',
                'confirmation_code': '123456',
                'new_password': 'NewPassword123',
                'confirm_new_password': 'NewPassword123'
            })
        }
        context = {}

        self.mock_client().confirm_forgot_password.side_effect = Exception('Some error')

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('An error occurred while resetting the password: Some error', response['body'])


if __name__ == '__main__':
    unittest.main() # pragma: no cover
