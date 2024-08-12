import json
import unittest
from unittest.mock import patch
from botocore.exceptions import ClientError, NoCredentialsError
from modules.users.delete_user_profile import app
from modules.users.delete_user_profile.app import delete_user_cognito
from modules.users.delete_user_profile.common.httpStatusCodeError import HttpStatusCodeError


class TestDeleteUserProfile(unittest.TestCase):

    @staticmethod
    def print_response(response):
        """Prints the status code and body of the response."""
        print("Status Code:", response['statusCode'])
        if 'body' in response:
            body = json.loads(response['body'])
            print("Response Body:", body)
        else:
            print("No body found in response")

    @staticmethod
    def print_exception(context):
        """Prints the status code and message of the captured exception."""
        print("Exception Status Code:", context.exception.status_code)
        print("Exception Message:", context.exception.message)

    @staticmethod
    def print_success(id_user, status_code):
        """Prints a success message indicating that the user was successfully deleted."""
        print(f"User with ID {id_user} deleted successfully with status code {status_code}")

    @patch('modules.users.delete_user_profile.app.delete_user_profile')
    @patch('modules.users.delete_user_profile.app.validate_body')
    @patch('modules.users.delete_user_profile.app.delete_user_cognito')
    @patch('modules.users.delete_user_profile.app.get_secret')
    def test_lambda_handler(self, mock_get_secret, mock_delete_user_cognito, mock_validate_body, mock_delete_user_profile):
        """Tests the lambda_handler function to ensure it correctly processes a successful case."""

        # Setup mocks
        mock_get_secret.return_value = {'USER_POOL_ID': 'mock_pool_id'}
        mock_validate_body.return_value = True
        mock_delete_user_cognito.return_value = True
        mock_delete_user_profile.return_value = True

        # Success request body
        body_user_successfully = {
            'body': json.dumps({'id_user': '123e4567-e89b-12d3-a456-426614174000'})
        }

        # Call lambda_handler function
        response = app.lambda_handler(body_user_successfully, None)
        expected_response = {
            'statusCode': 200,
            'body': json.dumps(f'User with id {json.loads(body_user_successfully["body"])["id_user"]} deleted successfully')
        }

        # Assertions
        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_user_successfully['body'])

    def test_id_user_is_missing(self):
        """Tests the lambda_handler function when the id_user is missing in the request body."""

        body_id_user_is_missing = {'body': json.dumps({})}
        response = app.lambda_handler(body_id_user_is_missing, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Id_user is required")
        }

        # Assertions
        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_id_user_is_missing['body'])

    def test_id_user_is_not_string(self):
        """Tests the lambda_handler function when the id_user is not a string."""

        body_id_user_is_not_string = {'body': json.dumps({'id_user': 12345})}
        response = app.lambda_handler(body_id_user_is_not_string, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Id_user must be a non-empty string")
        }

        # Assertions
        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_id_user_is_not_string['body'])

    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_success(self, mock_boto_session):
        """Tests the get_secret function to ensure it correctly retrieves the secret."""

        class MockClient:
            def get_secret_value(self, SecretId):
                return {'SecretString': json.dumps({'USER_POOL_ID': 'mock_pool_id'})}

        mock_boto_session.return_value.client.return_value = MockClient()

        secret = app.get_secret()
        expected_secret = {'USER_POOL_ID': 'mock_pool_id'}

        # Assertions
        self.assertEqual(secret, expected_secret)
        self.print_response({'statusCode': 200, 'body': json.dumps(secret)})

    @patch('modules.users.delete_user_profile.app.boto3.client')
    def test_get_secret_client_error(self, mock_boto_client):
        """Tests the get_secret function when a client error occurs."""

        class MockClient:
            def get_secret_value(self, SecretId):
                raise ClientError(
                    error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
                    operation_name='GetSecretValue'
                )

        mock_boto_client.return_value = MockClient()

        with self.assertRaises(HttpStatusCodeError) as context:
            app.get_secret()

        # Assertions
        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Error getting secret ->", context.exception.message)
        self.print_exception(context)

    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_no_credentials_error(self, mock_boto_session):
        """Tests the get_secret function when a credentials error occurs."""

        class MockClient:
            def get_secret_value(self, SecretId):
                raise NoCredentialsError()

        mock_boto_session.return_value.client.return_value = MockClient()

        with self.assertRaises(HttpStatusCodeError) as context:
            app.get_secret()

        # Assertions
        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Error getting secret ->", context.exception.message)
        self.print_exception(context)

    @patch('modules.users.delete_user_profile.app.get_db_connection')
    def test_delete_user_profile_success(self, mock_get_db_connection):
        """Tests the delete_user_profile function to ensure it successfully deletes a user."""

        class MockConnection:
            def cursor(self):
                class MockCursor:
                    def __enter__(self):
                        return self

                    def __exit__(self, exc_type, exc_value, traceback):
                        pass

                    def execute(self, query, params):
                        pass

                    @property
                    def rowcount(self):
                        return 1  # Simulates that one row was deleted

                return MockCursor()

            def commit(self):
                pass  # Simulates the commit method

            def close(self):
                pass

        mock_get_db_connection.return_value = MockConnection()

        id_user = '123e4567-e89b-12d3-a456-426614174000'

        # Call the function and verify that it behaves as expected
        result = app.delete_user_profile(id_user)
        self.assertTrue(result)
        self.print_success(id_user, 200)

    @patch('modules.users.delete_user_profile.app.get_db_connection')
    def test_delete_user_profile_not_found(self, mock_get_db_connection):
        """Tests the delete_user_profile function when the user is not found."""

        class MockConnection:
            def cursor(self):
                class MockCursor:
                    def __enter__(self):
                        return self

                    def __exit__(self, exc_type, exc_value, traceback):
                        pass

                    def execute(self, query, params):
                        pass

                    def commit(self):
                        pass

                    @property
                    def rowcount(self):
                        return 0  # Simulates that no rows were deleted

                return MockCursor()

            def close(self):
                pass

        mock_get_db_connection.return_value = MockConnection()

        id_user = '123e4567-e89b-12d3-a456-426614174000'

        with self.assertRaises(HttpStatusCodeError) as context:
            app.delete_user_profile(id_user)

        # Assertions
        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("User not found", context.exception.message)
        self.print_exception(context)

    @patch('modules.users.delete_user_profile.app.boto3.client')
    def test_delete_user_cognito_success(self, mock_boto_client):
        """Test for successful deletion of a user in Cognito."""
        mock_cognito = mock_boto_client.return_value
        mock_cognito.admin_delete_user.return_value = {}

        secrets = {'USER_POOL_ID': 'mock_pool_id'}
        id_user = 'testuser'

        result = delete_user_cognito(id_user, secrets)

        mock_cognito.admin_delete_user.assert_called_once_with(
            UserPoolId=secrets['USER_POOL_ID'],
            Username=id_user
        )
        self.assertTrue(result)

    @patch('modules.users.delete_user_profile.app.boto3.client')
    def test_delete_user_cognito_success(self, mock_boto_client):
        """Test for successful deletion of a user in Cognito."""
        mock_cognito = mock_boto_client.return_value
        mock_cognito.admin_delete_user.return_value = {}

        secrets = {'USER_POOL_ID': 'mock_pool_id'}
        id_user = 'testuser'

        result = delete_user_cognito(id_user, secrets)

        mock_cognito.admin_delete_user.assert_called_once_with(
            UserPoolId=secrets['USER_POOL_ID'],
            Username=id_user
        )
        self.assertTrue(result)

    @patch('modules.users.delete_user_profile.app.boto3.client')
    def test_delete_user_cognito_client_error(self, mock_boto_client):
        """Test for handling ClientError during deletion of a user in Cognito."""
        mock_cognito = mock_boto_client.return_value
        mock_cognito.admin_delete_user.side_effect = ClientError(
            error_response={'Error': {'Code': 'UserNotFoundException', 'Message': 'User not found'}},
            operation_name='AdminDeleteUser'
        )

        secrets = {'USER_POOL_ID': 'mock_pool_id'}
        id_user = 'testuser'

        with self.assertRaises(HttpStatusCodeError) as context:
            delete_user_cognito(id_user, secrets)

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("User not found in Cognito", context.exception.message)

    @patch('modules.users.delete_user_profile.app.boto3.client')
    def test_delete_user_cognito_no_credentials_error(self, mock_boto_client):
        """Test for handling NoCredentialsError during deletion of a user in Cognito."""
        mock_cognito = mock_boto_client.return_value
        mock_cognito.admin_delete_user.side_effect = NoCredentialsError()

        secrets = {'USER_POOL_ID': 'mock_pool_id'}
        id_user = 'testuser'

        with self.assertRaises(HttpStatusCodeError) as context:
            delete_user_cognito(id_user, secrets)

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("No credentials found", context.exception.message)

if __name__ == '__main__':
    unittest.main()
