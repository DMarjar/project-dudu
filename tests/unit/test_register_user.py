import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.register_user import app

EVENT = {
    'body': json.dumps({
        'email': '20213tn105@utez.edu.mx',
        'username': 'Gislane',
        'gender': 'M'
    })
}


class Test(unittest.TestCase):
    def test_lambda_handler(self):

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'], '"User registered successfully"')

    @patch('modules.users.register_user.app.get_db_connection')
    @patch('modules.users.register_user.app.save_user_cognito')
    def test_insert_user_db_exception(self, mock_save_user_cognito, mock_get_db_connection):
        mock_save_user_cognito.return_value = 'id_user'

        mock_connection = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.side_effect = Exception('Error')

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'],'"Error inserting user"')

    @patch('modules.users.register_user.app.get_db_connection')
    @patch('modules.users.register_user.app.save_user_db')
    @patch('modules.users.register_user.app.save_user_cognito')
    def test_give_basic_rewards_exception(self, mock_save_user_cognito, mock_save_user_db, mock_get_db_connection):
        mock_save_user_cognito.return_value = 'id_user'
        mock_save_user_db.return_value = True

        mock_connection = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.side_effect = Exception('Error')

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'],'"Error giving basic rewards"')

    """
    test_validate_body
        rise exceptions on all cases
    """
    def test_email_not_in_body(self):
        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'gender': 'M'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'],  '"email is required"')

    def test_email_is_none(self):
        event = {
            'body': json.dumps({
                'email': None,
                'username': 'Gislane',
                'gender': 'M'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"email is required"')

    def test_email_is_not_str(self):
        event = {
            'body': json.dumps({
                'email': 123,
                'username': 'Gislane',
                'gender': 'M'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"email must be a string"')

    def test_email_is_not_valid(self):
        event = {
            'body': json.dumps({
                'email': 'admin',
                'username': 'Gislane',
                'gender': 'M'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"Invalid email format"')

    def test_username_not_in_body(self):
        event = {
            'body': json.dumps({
                'email': 'emilio@gmail.com',
                'gender': 'H'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"username is required"')

    def test_username_is_none(self):
        event = {
            'body': json.dumps({
                'email': 'emilio@gmail.com',
                'username': None,
                'gender': 'H'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"username is required"')

    def test_username_is_not_str(self):
        event = {
            'body': json.dumps({
                'email': 'emilio@gmail.com',
                'username': 123,
                'gender': 'H'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"username must be a string"')

    def test_username_is_too_short(self):
        event = {
            'body': json.dumps({
                'email': 'emilio@gmail.com',
                'username': 'Em',
                'gender': 'H'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"username must be at least 3 characters long"')

    def test_username_is_too_long(self):
        event = {
            'body': json.dumps({
                'email': 'emilio@gmail.com',
                'username': 'EmilioEmilioEmilioEmilio',
                'gender': 'H'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"username must be at most 20 characters long"')

    def test_gender_not_in_body(self):
        event = {
            'body': json.dumps({
                'email': 'emilio@gmail.com',
                'username': 'Emilio'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"gender is required"')

    def test_gender_is_none(self):
        event = {
            'body': json.dumps({
                'email': 'emilio@gmail.com',
                'username': 'Emilio',
                'gender': None
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"gender is required"')

    def test_gender_is_not_valid(self):
        event = {
            'body': json.dumps({
                'email': 'emilio@gmail.com',
                'username': 'Emilio',
                'gender': 'X'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"invalid gender value, must be M or F"')


if __name__ == '__main__':
    unittest.main()