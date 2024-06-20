import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from modules.missions.get_one_mission.app import lambda_handler


class Test(TestCase):

    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_get_db_connection = patch('modules.missions.get_one_mission.app.get_db_connection').start()
        self.mock_get_db_connection.return_value = self.mock_connection

    def tearDown(self):
        patch.stopall()

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
    unittest.main()
