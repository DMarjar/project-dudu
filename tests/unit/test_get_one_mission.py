import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from modules.missions.get_one_mission.app import lambda_handler
from modules.missions.get_one_mission.common.db_connection import get_db_connection, get_secrets
from botocore.exceptions import ClientError


class Test(TestCase):

    def setUp(self):
        self.mock_get_secrets_patch = patch('modules.missions.get_one_mission.common.db_connection.get_secrets')
        self.mock_get_secrets = self.mock_get_secrets_patch.start()
        self.mock_cursor = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_get_db_connection = patch('modules.missions.get_one_mission.app.get_db_connection').start()
        self.mock_get_db_connection.return_value = self.mock_connection

    def tearDown(self):
        patch.stopall()

    @patch('boto3.session.Session.client')
    def test_get_secrets_success(self, mock_client):
        mock_secret_response = {
            'SecretString': '{"username": "test_user", "password": "test_password"}'
        }
        mock_client.return_value.get_secret_value.return_value = mock_secret_response
        secrets = get_secrets()
        self.assertEqual(secrets['username'], 'test_user')
        self.assertEqual(secrets['password'], 'test_password')
        mock_client.return_value.get_secret_value.assert_called_once_with(SecretId='dudu/db/connection')

    @patch('boto3.session.Session.client')
    def test_get_secrets_client_error(self, mock_client):
        mock_client.return_value.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'get_secret_value')
        with self.assertRaises(ClientError):
            get_secrets()

    @patch('boto3.session.Session.client')
    def test_get_secrets_exception_handling(self, mock_client):
        mock_client.return_value.get_secret_value.side_effect = Exception('Some error')
        with self.assertRaises(Exception):
            get_secrets()

    @patch('modules.missions.get_one_mission.common.db_connection.get_secrets')
    @patch('pymysql.connect')
    def test_get_db_connection_success(self, mock_connect, mock_get_secrets):
        mock_secrets = {
            'username': 'test_user',
            'password': 'test_password'
        }
        mock_get_secrets.return_value = mock_secrets
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        connection = get_db_connection()
        db_host = 'dududb.c7gis6w4srg8.us-east-2.rds.amazonaws.com'
        db_name = 'dududb'
        mock_get_secrets.assert_called_once()
        mock_connect.assert_called_once_with(
            host=db_host,
            user=mock_secrets['username'],
            password=mock_secrets['password'],
            db=db_name
        )
        self.assertEqual(connection, mock_connection)

    def test_lambda_handler_success(self):
        self.mock_cursor.fetchone.return_value = (1, 'Test Mission')
        self.mock_cursor.description = (('id_mission',), ('name',))
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor

        event = {
            'pathParameters': {
                'id_mission': 1
            }
        }

        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 200)
        self.assertIn('Test Mission', result['body'])

    def test_lambda_handler_mission_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        self.mock_cursor.description = (('id_mission',), ('name',))
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor

        event = {
            'pathParameters': {
                'id_mission': 1
            }
        }

        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 404)
        self.assertIn('Mission not found', result['body'])

    def test_lambda_handler_no_id_mission(self):
        event = {
            'pathParameters': {}
        }

        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 400)
        self.assertIn('Mission id is required', result['body'])

    def test_lambda_handler_exception(self):
        self.mock_get_db_connection.side_effect = Exception('Database error')

        event = {
            'pathParameters': {
                'id_mission': 1
            }
        }

        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertIn('An error occurred: Database error', result['body'])


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
