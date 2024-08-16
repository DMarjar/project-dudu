import json
import unittest
from unittest.mock import patch, MagicMock
from modules.missions.complete_mission.app import lambda_handler


class TestCompleteMission(unittest.TestCase):
    """
    Test class for the lambda_handler function
    """

    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_get_db_connection = patch('modules.missions.complete_mission.app.get_db_connection').start()
        self.mock_get_db_connection.return_value = self.mock_connection

    def tearDown(self):
        patch.stopall()

    def test_lambda_handler_missing_body(self):
        # Test missing body in event
        event = {}
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("Bad request: Body is required", response['body'])

    def test_lambda_handler_missing_ids(self):
        # Test missing id_mission and id_user
        event = {
            'body': json.dumps({})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("Bad request: Body is required", response['body'])

    def test_lambda_handler_invalid_ids(self):
        # Test invalid id_mission and id_user types
        event = {
            'body': json.dumps({
                'id_mission': 'invalid',
                'id_user': 123
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("Invalid mission or user ID", response['body'])

    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_lambda_handler_user_not_found(self, mock_get_db_connection):
        # Test when user is not found in the database
        mock_get_db_connection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = None

        event = {
            'body': json.dumps({
                'id_mission': 1,
                'id_user': "valid_user"
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("User not found", response['body'])

    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_lambda_handler_xp_limit_reached(self, mock_get_db_connection):
        # Test when user's XP is already at the limit
        mock_get_db_connection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (100, 100, 1)  # current_xp = xp_limit

        event = {
            'body': json.dumps({
                'id_mission': 1,
                'id_user': "valid_user"
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("User's XP is already at the limit", response['body'])

    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_lambda_handler_success(self, mock_get_db_connection):
        # Test successful completion of a mission and XP update
        mock_get_db_connection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (50, 100, 2)

        event = {
            'body': json.dumps({
                'id_mission': 1,
                'id_user': "valid_user"
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn("Mission 1 completed successfully and XP updated", json.loads(response['body'])['message'])

    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_lambda_handler_level_up(self, mock_get_db_connection):
        # Test level up scenario
        mock_get_db_connection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (95, 100, 4)

        event = {
            'body': json.dumps({
                'id_mission': 1,
                'id_user': "valid_user"
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertIn("Level Up!", response_body['message'])
        self.assertTrue(response_body['level_up'])

    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_lambda_handler_exception(self, mock_get_db_connection):
        # Test when there is an exception during the database operation
        mock_get_db_connection.side_effect = Exception("Database error")
        event = {
            'body': json.dumps({
                'id_mission': 1,
                'id_user': "valid_user"
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("An error occurred: Database error", response['body'])


if __name__ == '__main__':
    unittest.main()
