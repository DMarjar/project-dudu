import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.update_alexa_user import app
from unittest import TestCase

EVENT = {
    'body': json.dumps({
        'id_user': '11eb8500-4021-704c-672d-',
        'username': 'Atoferatofe'
    })
}


class Test(TestCase):
    @patch('modules.users.update_alexa_user.app.get_db_connection')
    def test_lambda_handler(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        response = app.lambda_handler(EVENT, None)
        self.assertIn(response['body'], ['true', 'false', True, False])

    def test_id_user_not_in_body(self):
        event_no_id_user = {
            'body': json.dumps({
                'username': 'Atoferatofe'
            })
        }

        response = app.lambda_handler(event_no_id_user, None)
        self.assertEqual(response['body'], '"id_user is required"')

    def test_username_not_in_body(self):
        event_no_username = {
            'body': json.dumps({
                'id_user': '11'
            })
        }

        response = app.lambda_handler(event_no_username, None)
        self.assertEqual(response['body'], '"username is required"')

    def test_exception_in_update_user(self):
        with patch('modules.users.update_alexa_user.app.update_user') as mock_update_user:
            mock_update_user.side_effect = Exception('Error')

            response = app.lambda_handler(EVENT, None)
            self.assertEqual(response['body'], '"Error"')


if __name__ == '__main__':
    unittest.main()

