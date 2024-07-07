import json
import unittest
from unittest import TestCase, mock
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from modules.missions.mission_expiration import app
from modules.missions.mission_expiration.common.db_connection import get_db_connection, get_secrets
from datetime import datetime, timedelta
from tests.unit.utils.test_utils import (get_mock_secret_response, patch_boto3_client, patch_db_connection,
                                         patch_get_secrets, configure_db_connection_test)


class TestMissionExpiration(TestCase):

    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_get_db_connection = patch_db_connection('modules.missions.mission_expiration.app').start()
        self.mock_get_db_connection.return_value = self.mock_connection

    def tearDown(self):
        patch.stopall()

    @patch_boto3_client()
    def test_get_secrets_client_error(self, mock_client):
        mock_client.return_value.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'get_secret_value')
        with self.assertRaises(ClientError):
            get_secrets()

    @patch_boto3_client()
    def test_get_secrets_success(self, mock_client):
        mock_client.return_value.get_secret_value.return_value = get_mock_secret_response()
        secrets = get_secrets()
        self.assertEqual(secrets['username'], 'test_user')
        self.assertEqual(secrets['password'], 'test_password')
        mock_client.return_value.get_secret_value.assert_called_once_with(SecretId='dudu/db/connection')

    @patch_boto3_client()
    def test_get_secrets_exception_handling(self, mock_client):
        mock_client.return_value.get_secret_value.side_effect = Exception('Some error')
        with self.assertRaises(Exception):
            get_secrets()

    @patch_get_secrets('modules.missions.mission_expiration.common.db_connection')
    @patch('pymysql.connect')
    def test_get_db_connection_success(self, mock_connect, mock_get_secrets_function):
        connection = configure_db_connection_test(mock_connect, mock_get_secrets_function, get_db_connection)
        self.assertEqual(connection, mock_connect.return_value)

    @patch('modules.missions.mission_expiration.app.check_and_update_expired_missions')
    def test_lambda_handler_success(self, mock_check_and_update_expired_missions):
        mock_check_and_update_expired_missions.return_value = None

        response = app.lambda_handler(None, None)

        self.assertEqual(response, {
            'statusCode': 200,
            'body': json.dumps("Missions' expiration checking done")
        })

    @patch('modules.missions.mission_expiration.app.check_and_update_expired_missions')
    def test_lambda_handler_exception(self, mock_check_and_update_expired_missions):
        mock_check_and_update_expired_missions.side_effect = Exception("Test exception")

        response = app.lambda_handler(None, None)

        self.assertEqual(response, {
            'statusCode': 500,
            'body': json.dumps("An error occurred while checking the missions: Test exception")
        })

    def test_check_and_update_expired_missions(self):
        self.mock_connection = mock.MagicMock()
        self.mock_cursor = mock.MagicMock()
        self.mock_get_db_connection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor

        current_time = datetime.now()
        missions = [
            {'id_mission': 1, 'due_date': (current_time - timedelta(days=1)).strftime('%Y-%m-%d')},
            {'id_mission': 2, 'due_date': (current_time + timedelta(days=1)).strftime('%Y-%m-%d')},
            {'id_mission': 3, 'due_date': (current_time - timedelta(days=1)).strftime('%Y-%m-%d')},
            {'id_mission': 4, 'due_date': (current_time - timedelta(days=1)).strftime('%Y-%m-%d')}
        ]

        self.mock_cursor.fetchall.return_value = missions

        app.check_and_update_expired_missions()

        expected_calls = [
            mock.call("UPDATE missions SET status = 'failed' WHERE id_mission = %s", (1,)),
            mock.call("UPDATE missions SET status = 'failed' WHERE id_mission = %s", (3,)),
            mock.call("UPDATE missions SET status = 'failed' WHERE id_mission = %s", (4,))
        ]
        self.mock_cursor.execute.assert_has_calls(expected_calls, any_order=True)
        self.mock_connection.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()  # pragma: no cover