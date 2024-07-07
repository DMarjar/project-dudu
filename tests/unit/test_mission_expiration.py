import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from modules.missions.mission_expiration import app
from modules.missions.mission_expiration.db_connection import get_secrets

from datetime import datetime, timedelta


class TestMissionExpiration(TestCase):

    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_get_db_connection = patch('modules.missions.mission_expiration.app.get_db_connection').start()
        self.mock_get_db_connection.return_value = self.mock_connection

    @patch('boto3.session.Session.client')
    def test_get_secrets_client_error(self, mock_client):
        mock_client.return_value.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'get_secret_value')
        with self.assertRaises(ClientError):
            get_secrets()

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
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor

        current_time = datetime.now()
        missions = [
            {'id_mission': 1, 'due_date': current_time - timedelta(days=1)},
            {'id_mission': 2, 'due_date': current_time + timedelta(days=1)},
            {'id_mission': 3, 'due_date': current_time - timedelta(days=1)},
            {'id_mission': 4, 'due_date': current_time - timedelta(days=1)}
        ]

        self.mock_cursor.fetchall.return_value = missions
        app.check_and_update_expired_missions()
        expected_calls = [
            ('UPDATE missions SET status = %s WHERE id_mission = %s', ('failed', 1)),
        ]
        for call_args, expected_values in expected_calls:
            self.mock_cursor.execute.assert_any_call(call_args, expected_values)


if __name__ == '__main__':
    unittest.main() # pragma: no cover
