import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from modules.missions.get_one_mission.app import lambda_handler


class Test(TestCase):

    @patch('modules.missions.get_one_mission.app.get_db_connection')
    def test_lambda_handler_success(self, mock_get_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 'Test Mission')
        mock_cursor.description = (('id_mission',), ('name',))

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_connection

        event = {
            'pathParameters': {
                'id_mission': 1
            }
        }

        # Act
        result = lambda_handler(event, None)

        # Assert
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('Test Mission', result['body'])

    @patch('modules.missions.get_one_mission.app.get_db_connection')
    def test_lambda_handler_mission_not_found(self, mock_get_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.description = (('id_mission',), ('name',))

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_connection

        event = {
            'pathParameters': {
                'id_mission': 1
            }
        }

        # Act
        result = lambda_handler(event, None)

        # Assert
        self.assertEqual(result['statusCode'], 404)
        self.assertIn('Mission not found', result['body'])

    @patch('modules.missions.get_one_mission.app.get_db_connection')
    def test_lambda_handler_no_id_mission(self, mock_get_db_connection):
        # Arrange
        event = {
            'pathParameters': {}
        }

        # Act
        result = lambda_handler(event, None)

        # Assert
        self.assertEqual(result['statusCode'], 500)
        self.assertIn('id_mission is required', result['body'])

    @patch('modules.missions.get_one_mission.app.get_db_connection')
    def test_lambda_handler_exception(self, mock_get_db_connection):
        # Arrange
        mock_get_db_connection.side_effect = Exception('Database error')

        event = {
            'pathParameters': {
                'id_mission': 1
            }
        }

        # Act
        result = lambda_handler(event, None)

        # Assert
        self.assertEqual(result['statusCode'], 500)
        self.assertIn('An error occurred: Database error', result['body'])


if __name__ == '__main__':
    unittest.main()
