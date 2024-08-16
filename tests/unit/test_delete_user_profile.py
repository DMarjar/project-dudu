import json
import unittest
from unittest.mock import patch, MagicMock, Mock

import boto3
import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from modules.users.delete_user_profile import app
from modules.users.delete_user_profile.app import validate_body_for_deletion, delete_cognito_user, delete_user_db, \
    lambda_handler, get_username_from_sub, get_secret
from modules.users.delete_user_profile.common.db_connection import get_db_connection
from modules.users.delete_user_profile.common.httpStatusCodeError import HttpStatusCodeError


# Clase que simula el cliente de boto3
class MockCognitoClient:
    def __init__(self):
        self.users = {}

    def list_users(self, UserPoolId, Filter):
        # Simula el comportamiento del método list_users
        sub_value = Filter.split('"')[1]  # Extrae el valor del sub
        for user in self.users.values():
            if user.get('sub') == sub_value:
                return {'Users': [{'Username': user['username']}]}
        return {'Users': []}

    def admin_create_user(self, UserPoolId, Username, UserAttributes):
        sub = next((attr['Value'] for attr in UserAttributes if attr['Name'] == 'sub'), None)
        self.users[sub] = {'username': Username, 'sub': sub}

# Función que se está probando
def get_username_from_sub(sub, user_pool_id, client=None):
    client = client or boto3.client("cognito-idp", region_name="us-east-1")
    response = client.list_users(
        UserPoolId=user_pool_id,
        Filter=f'sub="{sub}"'
    )
    users = response.get('Users', [])
    if users:
        return users[0].get('Username')
    return None

#clase que simula una conexión a bd que siempre falla
class MockConnection:
    def cursor(self):
        raise Exception("Simulated database error")
    def close(self):
        pass


class TestDeleteUserProfile(unittest.TestCase):
    def setUp(self):
        # Configurar el cliente simulado
        self.client = MockCognitoClient()
        self.user_pool_id = 'test_pool_id'
        self.client.admin_create_user(
            UserPoolId=self.user_pool_id,
            Username="test_user",
            UserAttributes=[
                {"Name": "sub", "Value": "test_sub"}
            ],
        )

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


    """Test to ensure the delete_user_db function deletes a user successfully from the database"""
    @patch('modules.users.delete_user_profile.common.db_connection.get_secrets')
    @patch('modules.users.delete_user_profile.app.get_db_connection')
    def test_delete_user_db(self, mock_get_db_connection, mock_get_secrets):
        # Simulamos la respuesta del secreto
        mock_get_secrets.return_value = {'DB_HOST': 'mock_host', 'DB_USER': 'mock_user', 'DB_PASSWORD': 'mock_password'}
        # Simulamos la conexión de la base de datos
        mock_get_db_connection.return_value = MockConnection()

        id_user = "test_id_user"
        with pytest.raises(HttpStatusCodeError) as excinfo:
            delete_user_db(id_user)

        assert excinfo.value.status_code == 500
        assert "Database SQL Error" in str(excinfo.value)
        print(f"Test Passed: delete_user_db Exception - {str(excinfo.value)}")

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

    @patch('modules.users.delete_user_profile.app.delete_cognito_user')
    @patch('modules.users.delete_user_profile.app.get_db_connection')
    @patch('modules.users.delete_user_profile.app.get_secret')
    @patch('modules.users.delete_user_profile.app.validate_body_for_deletion')
    def test_lambda_handler_success(self, mock_validate_body, mock_get_secret, mock_get_db_connection,
                                    mock_delete_cognito_user):
        # Mocking the validation function to pass
        mock_validate_body.return_value = True

        # Mocking the secrets retrieval
        mock_get_secret.return_value = {'USER_POOL_ID': 'us-east-2_example'}

        # Mocking the database connection
        mock_connection = Mock()
        mock_cursor = MagicMock()

        # Configurar el cursor para manejar el contexto de administrador
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Asignar el cursor al método cursor del mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_connection

        # Mocking the deletion function in Cognito to do nothing
        mock_delete_cognito_user.return_value = None

        # Creating a test event
        event = {
            'body': json.dumps({
                'sub': '814b85d0-7001-7093-a1e1-0412495ca7a3',
                'id_user': '814b85d0-7001-7093-a1e1-0412495ca7a3'
            })
        }
        context = {}  # Mock context if necessary

        # Running the handler
        response = lambda_handler(event, context)

        # Assertions to verify behavior
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('User deleted successfully', response['body'])
        mock_validate_body.assert_called_once()
        mock_delete_cognito_user.assert_called_once_with('814b85d0-7001-7093-a1e1-0412495ca7a3',
                                                         {'USER_POOL_ID': 'us-east-2_example'})
        mock_get_db_connection.assert_called_once()

        # Check if the database operations were called
        mock_cursor.execute.assert_any_call("DELETE FROM user_rewards WHERE id_user = %s",
                                            ('814b85d0-7001-7093-a1e1-0412495ca7a3',))
        mock_cursor.execute.assert_any_call("DELETE FROM users WHERE id_user = %s",
                                            ('814b85d0-7001-7093-a1e1-0412495ca7a3',))
        mock_connection.commit.assert_called_once()

        print("Test Passed: Successful user deletion")

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
        # Ejecutar la función con el cliente simulado
        username = get_username_from_sub("test_sub", self.user_pool_id, client=self.client)
        self.assertEqual(username, "test_user")

    """Test get_username_from_sub_failure function"""
    def test_get_username_from_sub_failure(self):
        # Caso donde el sub no existe
        username = get_username_from_sub("non_existent_sub", self.user_pool_id, client=self.client)
        self.assertIsNone(username)

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
