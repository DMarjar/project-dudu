import json
from modules.users.exist_user import app
import unittest
from unittest.mock import patch, MagicMock
import pytest

EVENT = {
    'body': json.dumps({
        'id_user': '11eb8500-4021-704c-672d-',
    })
}


class Test(unittest.TestCase):

    @patch('modules.users.exist_user.app.get_db_connection')
    def test_lambda_handler(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        response = app.lambda_handler(EVENT, None)
        self.assertIn(response['body'], ['true', 'false', True, False])

    def test_id_user_not_in_body(self):
        event_no_id_user = {
            'body': json.dumps({})
        }

        response = app.lambda_handler(event_no_id_user, None)
        self.assertEqual(response['body'], '"id_user is required"')

    @patch('modules.users.exist_user.app.check_user_exists')
    def test_exception_in_check_user_exists(self, mock_check_user_existence):
        mock_check_user_existence.side_effect = Exception('Error')

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'], '"Error"')


if __name__ == '__main__':
    unittest.main()