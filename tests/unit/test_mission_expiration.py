import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from modules.missions.mission_expiration import app
from modules.missions.mission_expiration.common.db_connection import get_secrets

from datetime import datetime, timedelta


class TestMissionExpiration(TestCase):

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

    @patch('modules.missions.mission_expiration.common.db_connection.get_db_connection')
    def test_check_and_update_expired_missions(self, mock_get_db_connection):
        # Mock database cursor and execute method
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock missions data
        current_time = datetime.now()
        missions = [
            {'id_mission': 1, 'creation_date': current_time - timedelta(days=2), 'due_date': current_time - timedelta(days=1)},
            # Should fail
            {'id_mission': 2, 'creation_date': current_time - timedelta(days=2), 'due_date': current_time + timedelta(days=1)},
            # Should not fail
            {'id_mission': 3, 'creation_date': None, 'due_date': current_time - timedelta(days=1)},
            # Should not fail due to None creation_date
            {'id_mission': 4, 'creation_date': current_time, 'due_date': current_time - timedelta(days=1)},
            # Should not fail due to creation_date >= due_date
        ]

        mock_cursor.fetchall.return_value = missions

        app.check_and_update_expired_missions()


if __name__ == '__main__':
    unittest.main() # pragma: no cover
