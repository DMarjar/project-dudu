import json
import unittest
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError, NoCredentialsError
from pymysql import ProgrammingError

from modules.users.delete_user_profile import app
from modules.users.delete_user_profile.common.httpStatusCodeError import HttpStatusCodeError


class TestDeleteUserProfile(unittest.TestCase):

    @staticmethod
    def print_response(response):
        print("Status Code:", response['statusCode'])

        if 'body' in response:
            body = json.loads(response['body'])
            print("Response Body:", body)
        else:
            print("No body found in response")

    staticmethod
    def print_exception(self, context):
        print("Exception Status Code:", context.exception.status_code)
        print("Exception Message:", context.exception.message)

    @staticmethod
    def print_success(username, status_code):
        print(f"User {username} deleted successfully from Cognito with status code {status_code}")

    @staticmethod
    def print_success_bd(id):
        print(f"User with ID {id} deleted successfully from DB")

    """
    Test class for the lambda_handler function on the case is successful
    """

    @patch('modules.users.delete_user_profile.app.delete_user_profile')
    @patch('modules.users.delete_user_profile.app.validate_body')
    @patch('modules.users.delete_user_profile.app.delete_user_cognito')
    @patch('modules.users.delete_user_profile.app.get_secret')
    def test_lambda_handler(self, mock_get_secret, mock_delete_user_cognito, mock_validate_body, mock_delete_user_profile):
        mock_get_secret.return_value = {
            'USER_POOL_ID': 'mock_pool_id'
        }

        mock_validate_body.return_value = True
        mock_delete_user_cognito.return_value = True
        mock_delete_user_profile.return_value = True

        body_user_successfully = {
            'body': json.dumps({
                'id': 1,
                'username': 'testuser'
            })
        }
        response = app.lambda_handler(body_user_successfully, None)
        expected_response = {
            'statusCode': 200,
            'body': json.dumps(f'User with id {json.loads(body_user_successfully["body"])["id"]} deleted successfully')
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_user_successfully['body'])

    """
    Test class for the lambda_handler function on:
        - the case where the id is required
        - the case where the id must be a non-empty int
    """

    def test_id_user_is_missing(self):
        body_id_user_is_missing = {
            'body': json.dumps({})
        }
        response = app.lambda_handler(body_id_user_is_missing, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Id is required")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_id_user_is_missing['body'])

    def test_id_user_is_not_int(self):
        body_id_user_is_not_int = {
            'body': json.dumps({
                'id': 'not_an_int',
            })
        }
        response = app.lambda_handler(body_id_user_is_not_int, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Id must be a non-empty int")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_id_user_is_not_int['body'])

    """
    Test class for the lambda_handler function on:
        - the case where the username not in body
        - the case where the username is none
        - the case where the username must be a string
    """

    def test_username_is_missing(self):
        body_username_is_missing = {
            'body': json.dumps({
                'id': 1,
            })
        }
        response = app.lambda_handler(body_username_is_missing, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Username not in body, is required")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_username_is_missing['body'])

    def test_username_is_none(self):
        body_username_is_none = {
            'body': json.dumps({
                'id': 1,
                'username': None
            })
        }
        response = app.lambda_handler(body_username_is_none, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Username is none, is required")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_username_is_none['body'])

    def test_username_is_not_string(self):
        body_username_is_not_string = {
            'body': json.dumps({
                'id': 1,
                'username': 12345,
            })
        }
        response = app.lambda_handler(body_username_is_not_string, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Username must be a string")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_username_is_not_string['body'])

    """
    Test class for the get_secret function on:
        - the case where is success
        - the case where there is secret client error
        - the case where is secret credentials error
    """

    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_success(self, mock_boto_session):
        mock_boto_client = MagicMock()
        mock_boto_session.return_value.client.return_value = mock_boto_client

        mock_boto_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'USER_POOL_ID': 'mock_pool_id'
            })
        }

        secret = app.get_secret()
        expected_secret = {
            'USER_POOL_ID': 'mock_pool_id'
        }

        self.assertEqual(secret, expected_secret)
        self.print_response({'statusCode': 200, 'body': json.dumps(secret)})

    @patch('modules.users.delete_user_profile.app.boto3.client')
    def test_get_secret_client_error(self, mock_boto_client):
        mock_secrets_manager_client = MagicMock()
        mock_boto_client.return_value = mock_secrets_manager_client

        mock_secrets_manager_client.get_secret_value.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            operation_name='GetSecretValue'
        )

        with self.assertRaises(HttpStatusCodeError) as context:
            app.get_secret()

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Error getting secret ->", context.exception.message)
        self.print_exception(context)

    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_no_credentials_error(self, mock_boto_session):
        mock_boto_client = MagicMock()
        mock_boto_session.return_value.client.return_value = mock_boto_client

        mock_boto_client.get_secret_value.side_effect = NoCredentialsError()

        with self.assertRaises(HttpStatusCodeError) as context:
            app.get_secret()

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Error getting secret ->", context.exception.message)
        self.print_exception(context)

    """
    Test class for the delete_user_cognito function on:
        - the case where delete user cognito is success
        - the case where there is cognito client error
    """
    @patch('modules.users.delete_user_profile.app.boto3.client')
    def test_delete_user_cognito_success(self, mock_boto_client):
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client

        username = 'testuser'
        secrets = {'USER_POOL_ID': 'mock_pool_id'}

        app.delete_user_cognito(username, secrets)

        mock_cognito_client.admin_delete_user.assert_called_once_with(
            UserPoolId='mock_pool_id',
            Username=username
        )

        self.print_success(username, 200)
    @patch('modules.users.delete_user_profile.app.boto3.client')
    def test_delete_user_cognito_client_error(self, mock_boto_client):
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client

        mock_cognito_client.admin_delete_user.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'User not found'}},
            operation_name='AdminDeleteUser'
        )

        username = 'testuser'
        secrets = {'USER_POOL_ID': 'mock_pool_id'}

        with self.assertRaises(HttpStatusCodeError) as context:
            app.delete_user_cognito(username, secrets)

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Error deleting user from Cognito ->", context.exception.message)
        self.print_exception(context)

    """
    Test class for the delete_user_profile function on:
        - the case where delete user profile is success
        - the case where user profile not found
    """
    @patch('modules.users.delete_user_profile.app.get_db_connection')
    def test_delete_user_profile_success(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_get_db_connection.return_value = mock_connection

        id = 1

        app.delete_user_profile(id)

        mock_connection.cursor.assert_called_once()
        mock_connection.commit.assert_called_once()

        self.print_success_bd(id)

    @patch('modules.users.delete_user_profile.app.get_db_connection')
    def test_delete_user_profile_not_found(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_get_db_connection.return_value = mock_connection

        id = 1
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.__enter__.return_value = mock_cursor  
        mock_cursor.rowcount = 0

        with self.assertRaises(HttpStatusCodeError) as context:
            app.delete_user_profile(id)

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("User not found", context.exception.message)
        self.print_exception(context)

if __name__ == '__main__':
    unittest.main()