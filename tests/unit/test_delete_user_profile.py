import json
import unittest
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from modules.users.delete_user_profile import app
from modules.users.delete_user_profile.app import validate_body_for_deletion, delete_cognito_user, delete_user_db, \
    lambda_handler, get_username_from_sub, get_secret
from modules.users.delete_user_profile.common.db_connection import get_db_connection
from modules.users.delete_user_profile.common.httpStatusCodeError import HttpStatusCodeError


# Clase que simula el cliente de boto3
class MockCognitoClient:
    def list_users(self, UserPoolId, Filter):
        return {'Users': []}

#clase que simula una conexión a bd que siempre falla
class MockConnection:
    def cursor(self):
        raise Exception("Simulated database error")
    def close(self):
        pass


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


    """Test to ensure the validate_body_for_deletion function works with a valid body"""
    def test_validate_body_for_deletion_valid(self):
        body = {"sub": "valid_sub", "id_user": "valid_id_user"}
        assert validate_body_for_deletion(body) == True
        print("Test Passed: Valid body for deletion")


    """Test to ensure the validate_body_for_deletion function raises an error when 'sub' is missing"""
    def test_validate_body_for_deletion_missing_sub(self):
        body = {"id_user": "valid_id_user"}
        with pytest.raises(HttpStatusCodeError) as e:
            validate_body_for_deletion(body)
        assert e.value.status_code == 400
        print(f"Test Passed: Missing sub - Status Code: {e.value.status_code}")
        assert "sub is required" in str(e.value)


    """Test to ensure the validate_body_for_deletion function raises an error when 'id_user' is empty"""
    def test_validate_body_for_deletion_empty_id_user(self):
        body = {"sub": "valid_sub", "id_user": ""}
        with pytest.raises(HttpStatusCodeError) as e:
            validate_body_for_deletion(body)
        assert e.value.status_code == 400
        print(f"Test Passed: Empty id_user - Status Code: {e.value.status_code}")
        assert "id_user is required" in str(e.value)


    """Test to ensure the database connection is established and not None"""
    def test_get_db_connection(self):
        connection = get_db_connection()
        assert connection is not None
        print("Test Passed: Database connection established")
        connection.close()


    """Test to ensure the delete_user_db function deletes a user successfully from the database"""
    def test_delete_user_db(self):
        # Add a test user to the database before running the test
        id_user = "test_id_user"
        try:
            delete_user_db(id_user)
            print("Test Passed: Database user deleted successfully")
            # You could add a query here to verify the user was indeed deleted
        except Exception as e:
            pytest.fail(f"Unexpected error: {str(e)}")

    """Test get_secret function"""
    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_success(self, mock_boto_session):
        class MockClient:
            def get_secret_value(self, SecretId):
                return {'SecretString': json.dumps({'USER_POOL_ID': 'mock_pool_id'})}
        mock_boto_session.return_value.client.return_value = MockClient()
        secret = app.get_secret()
        expected_secret = {'USER_POOL_ID': 'mock_pool_id'}
        self.assertEqual(secret, expected_secret)
        self.print_response({'statusCode': 200, 'body': json.dumps(secret)})

    """Test lambda_handler function"""
    def test_lambda_handler_success(self):
        event = {
            'body': json.dumps({
                'sub': '91bb4550-c0e1-7042-eb96-d77a5247ba23',
                'id_user': '91bb4550-c0e1-7042-eb96-d77a5247ba23'
            })
        }
        context = {}  # Mock context if needed
        response = lambda_handler(event, context)
        print("Status Code:", response['statusCode'])
        print("Response Body:", json.loads(response['body']))
        assert response['statusCode'] == 200
        assert json.loads(response['body']) == "User deleted successfully"

    """Test lambda_handler function with invalid input"""
    def test_lambda_handler_invalid_input(self):
        event = {
            'body': json.dumps({
                'sub': 'valid_sub'
                # Missing 'id_user'
            })
        }
        context = {}  # Mock context if needed
        response = lambda_handler(event, context)
        print("Status Code:", response['statusCode'])
        print("Response Body:", json.loads(response['body']))
        assert response['statusCode'] == 400
        assert "id_user is required" in json.loads(response['body'])['message']

    """Test lambda_handler function with AWS ClientError"""
    @patch('modules.users.delete_user_profile.app.delete_cognito_user',
           side_effect=ClientError({'Error': {'Code': 'ClientError'}}, 'operation'))
    @patch('modules.users.delete_user_profile.app.get_secret', return_value={'USER_POOL_ID': 'mock_pool_id'})
    def test_lambda_handler_client_error(self, mock_get_secret, mock_delete_cognito_user):
        event = {
            'body': json.dumps({
                'sub': 'a1cb1570-90c1-70d9-1031-b84d8a91beea',
                'id_user': 'a1cb1570-90c1-70d9-1031-b84d8a91beea'
            })
        }
        context = {}  # Mock context if needed
        response = lambda_handler(event, context)
        print("Status Code:", response['statusCode'])
        print("Response Body:", json.loads(response['body']))
        assert response['statusCode'] == 500
        assert "AWS Client Error" in json.loads(response['body'])['message']

    """Test lambda_handler function with NoCredentialsError"""

    @patch('modules.users.delete_user_profile.app.delete_cognito_user', side_effect=NoCredentialsError)
    @patch('modules.users.delete_user_profile.app.get_secret', return_value={'USER_POOL_ID': 'mock_pool_id'})
    def test_lambda_handler_no_credentials_error(self, mock_get_secret, mock_delete_cognito_user):
        event = {
            'body': json.dumps({
                'sub': 'a1cb1570-90c1-70d9-1031-b84d8a91beea',
                'id_user': 'a1cb1570-90c1-70d9-1031-b84d8a91beea'
            })
        }
        context = {}  # Mock context if needed
        response = lambda_handler(event, context)
        print("Status Code:", response['statusCode'])
        print("Response Body:", json.loads(response['body']))
        assert response['statusCode'] == 500
        assert "Credentials Error" in json.loads(response['body'])['message']

    """Test lambda_handler function with unexpected exception"""

    @patch('modules.users.delete_user_profile.app.delete_cognito_user', side_effect=Exception("Unexpected error"))
    @patch('modules.users.delete_user_profile.app.get_secret', return_value={'USER_POOL_ID': 'mock_pool_id'})
    def test_lambda_handler_unexpected_exception(self, mock_get_secret, mock_delete_cognito_user):
        event = {
            'body': json.dumps({
                'sub': 'a1cb1570-90c1-70d9-1031-b84d8a91beea',
                'id_user': 'a1cb1570-90c1-70d9-1031-b84d8a91beea'
            })
        }
        context = {}  # Mock context if needed
        response = lambda_handler(event, context)
        print("Status Code:", response['statusCode'])
        print("Response Body:", json.loads(response['body']))
        assert response['statusCode'] == 500
        assert "An unexpected error occurred" in json.loads(response['body'])['message']

    """Test get_username_from_sub function"""
    def test_get_username_from_sub_success(self):
        user_pool_id = "us-east-2_EXoNvoJRZ"
        sub = "91bb4550-c0e1-7042-eb96-d77a5247ba23"
        try:
            username = get_username_from_sub(sub, user_pool_id)
            print(f"Username retrieved: {username}")
            self.assertIsNotNone(username)
            # Add further assertions based on expected values
            print("Test Passed: Username retrieved successfully")
        except Exception as e:
            self.fail(f"Unexpected error: {str(e)}")

    """Tests the get_secret function to ensure it correctly retrieves the secret."""
    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_success(self, mock_boto_session):
        class MockClient:
            def get_secret_value(self, SecretId):
                return {'SecretString': json.dumps({'USER_POOL_ID': 'mock_pool_id'})}

        mock_boto_session.return_value.client.return_value = MockClient()

        secret = app.get_secret()
        expected_secret = {'USER_POOL_ID': 'mock_pool_id'}

        # Assertions
        self.assertEqual(secret, expected_secret)
        self.print_response({'statusCode': 200, 'body': json.dumps(secret)})

    """Test get_secret function success"""
    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_success(self, mock_boto_session):
        class MockClient:
            def get_secret_value(self, SecretId):
                return {'SecretString': json.dumps({'USER_POOL_ID': 'mock_pool_id'})}

        mock_boto_session.return_value.client.return_value = MockClient()
        secret = get_secret()
        expected_secret = {'USER_POOL_ID': 'mock_pool_id'}
        self.assertEqual(secret, expected_secret)
        print("Test Passed: Secret retrieved successfully")

    """Test get_secret function with ClientError"""
    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_client_error(self, mock_boto_session):
        class MockClient:
            def get_secret_value(self, SecretId):
                raise ClientError({'Error': {'Code': 'ClientError'}}, 'operation')

        mock_boto_session.return_value.client.return_value = MockClient()
        with self.assertRaises(HttpStatusCodeError) as e:
            get_secret()
        self.assertEqual(e.exception.status_code, 500)
        self.assertTrue("Error getting secret from AWS Secrets Manager" in str(e.exception))
        print(f"Test Passed: get_secret ClientError - {str(e.exception)}")

    """Test get_secret function with NoCredentialsError"""
    @patch('modules.users.delete_user_profile.app.boto3.session.Session')
    def test_get_secret_no_credentials_error(self, mock_boto_session):
        class MockClient:
            def get_secret_value(self, SecretId):
                raise NoCredentialsError

        mock_boto_session.return_value.client.return_value = MockClient()
        with self.assertRaises(HttpStatusCodeError) as e:
            get_secret()
        self.assertEqual(e.exception.status_code, 500)
        self.assertTrue("AWS Credentials Error" in str(e.exception))
        print(f"Test Passed: get_secret NoCredentialsError - {str(e.exception)}")

    """Test to define a test function to verify the behavior when the user is not present"""
    def test_get_username_from_sub_user_not_found(self):
        with patch('modules.users.delete_user_profile.app.boto3.client') as mock_boto_client:
            mock_boto_client.return_value = MockCognitoClient()

            with pytest.raises(Exception) as excinfo:
                get_username_from_sub("a1cb1570-90c1-70d9-1031-b84d8a91beea", "us-east-2_EXoNvoJRZ")

            assert str(excinfo.value) == "User not found"
            print(f"Test Passed: get_username_from_sub User Not Found - {str(excinfo.value)}")

    """Test to define a test function to simulate an error in the database"""
    def test_delete_user_db_exception(self):
        with patch('modules.users.delete_user_profile.app.get_db_connection', return_value=MockConnection()):
            with pytest.raises(HttpStatusCodeError) as excinfo:
                delete_user_db("test_id_user")

            assert excinfo.value.status_code == 500
            assert "Database SQL Error" in str(excinfo.value)
            print(f"Test Passed: delete_user_db Exception - {str(excinfo.value)}")

if __name__ == '__main__':
    unittest.main()
