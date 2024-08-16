import json
import json
import unittest
from unittest.mock import patch, MagicMock
from modules.missions.mission_expiration import app
from unittest import TestCase


class TestMissionExpiration(TestCase):

    @patch('modules.missions.mission_expiration.app.get_db_connection')
    def test_lambda_success(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{'id_mission': 1, 'due_date': '2021-12-12'}]

        response = app.lambda_handler({}, None)
        self.assertEqual(response['statusCode'], 200)

    @patch('modules.missions.mission_expiration.app.get_db_connection')
    def test_lambda_exception(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.side_effect = Exception('Error')

        response = app.lambda_handler({}, None)
        self.assertEqual(response['statusCode'], 500)


if __name__ == '__main__':
    unittest.main()