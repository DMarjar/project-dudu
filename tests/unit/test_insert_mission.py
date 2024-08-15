import json
import unittest
from unittest.mock import patch, MagicMock
from modules.missions.insert_mission import app

EVENT = {
    'body': json.dumps({
        'original_description': 'test',
        'id_user': 1,
        'creation_date': '2022-01-01',
        'due_date': '2022-01-01',
        'status': 'pending'
    })
}


class Test(unittest.TestCase):

    @patch('modules.missions.insert_mission.app.insert_mission')
    @patch('modules.missions.insert_mission.app.get_openai_client')
    @patch('modules.missions.insert_mission.app.validate_user')
    @patch('modules.missions.insert_mission.common.db_connection.get_secrets')
    def test_success_lambda_handler(self, mock_get_secrets, mock_validate_user, mock_get_openai_client, mock_insert_mission):
        mock_get_secrets.return_value = {
            'username': 'admin',
            'password': 'admin',
            'engine': 'admin',
            'host': 'admin',
            'port': 'admin',
            'dbname': 'admin',
            'dbInstanceIdentifier': 'admin'
        }

        mock_validate_user.return_value = True
        mock_get_openai_client.return_value = 'fantasy description'
        mock_insert_mission.return_value = True

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'], '"fantasy description"')

    def test_no_original_description(self):
        body_no_original_description = {
            'body': json.dumps({
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_no_original_description, None)
        self.assertEqual(response['body'], '"original_description is required"')

    def test_original_description_is_none(self):
        body_original_description_is_none = {
            'body': json.dumps({
                'original_description': None,
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_original_description_is_none, None)
        self.assertEqual(response['body'], '"original_description is required"')

    def test_original_description_is_not_string(self):
        body_original_description_is_not_string = {
            'body': json.dumps({
                'original_description': 123,
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_original_description_is_not_string, None)
        self.assertEqual(response['body'], '"original_description must be a string"')

    def test_original_description_is_empty_string(self):
        body_original_description_is_empty_string = {
            'body': json.dumps({
                'original_description': '',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_original_description_is_empty_string, None)
        self.assertEqual(response['body'], '"original_description cannot be empty"')

    def test_no_id_user(self):
        body_no_id_user = {
            'body': json.dumps({
                'original_description': 'test',
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_no_id_user, None)
        self.assertEqual(response['body'], '"id_user is required"')

    def test_id_user_is_none(self):
        body_id_user_is_none = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': None,
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_id_user_is_none, None)
        self.assertEqual(response['body'], '"id_user is required"')

    def test_no_creation_date(self):
        body_no_creation_date = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_no_creation_date, None)
        self.assertEqual(response['body'], '"creation_date is required"')

    def test_creation_date_is_none(self):
        body_creation_date_is_none = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': None,
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_creation_date_is_none, None)
        self.assertEqual(response['body'], '"creation_date is required"')

    def test_creation_date_is_incorrect_format(self):
        body_creation_date_is_incorrect_format = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '01-01-2022',
                'due_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_creation_date_is_incorrect_format, None)
        self.assertEqual(response['body'], '"Incorrect creation_date format, should be YYYY-MM-DD"')


    def test_no_due_date(self):
        body_no_due_date = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_no_due_date, None)
        self.assertEqual(response['body'], '"due_date is required"')

    def test_due_date_is_none(self):
        body_due_date_is_none = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': None,
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_due_date_is_none, None)
        self.assertEqual(response['body'], '"due_date is required"')

    def test_due_date_is_incorrect_format(self):
        body_due_date_is_incorrect_format = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': '01-01-2022',
                'status': 'pending'
            })
        }

        response = app.lambda_handler(body_due_date_is_incorrect_format, None)
        self.assertEqual(response['body'], '"Incorrect due_date format, should be YYYY-MM-DD"')

    def test_no_status(self):
        body_no_status = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
            })
        }

        response = app.lambda_handler(body_no_status, None)
        self.assertEqual(response['body'], '"status is required"')

    def test_status_is_none(self):
        body_status_is_none = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
                'status': None
            })
        }

        response = app.lambda_handler(body_status_is_none, None)
        self.assertEqual(response['body'], '"status is required"')

    def test_status_is_invalid(self):
        body_status_is_invalid = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'due_date': '2022-01-01',
                'status': 'invalid'
            })
        }

        response = app.lambda_handler(body_status_is_invalid, None)
        self.assertEqual(response['body'], '"Invalid status"')

    def test_get_secrets_exception(self):
        with patch('modules.missions.insert_mission.common.db_connection.get_secrets',
                   side_effect=Exception('Error getting secret')):
            response = app.lambda_handler(EVENT, None)
            self.assertEqual(response['body'], '"Error getting secret"')

    @patch('modules.missions.insert_mission.common.db_connection.get_secrets')
    def test_db_connection_exception(self, mock_get_secrets):
        mock_get_secrets.return_value = {
            'username': 'admin',
            'password': 'admin',
            'engine': 'admin',
            'host': 'admin',
            'port': 'admin',
            'dbname': 'admin',
            'dbInstanceIdentifier': 'admin'
        }

        with patch('modules.missions.insert_mission.common.db_connection.get_db_connection',
                   side_effect=Exception('Error connecting to database')):
            response = app.lambda_handler(EVENT, None)
            self.assertEqual(response['body'], '"Error connecting to database"')

    @patch('modules.missions.insert_mission.app.insert_mission')
    @patch('modules.missions.insert_mission.app.get_openai_client')
    @patch('modules.missions.insert_mission.app.get_db_connection')
    def test_validate_user_success(self, mock_get_db_connection, mock_get_openai_client, mock_insert_mission):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{'id_user': 1, 'name': 'John Doe'}]

        mock_get_openai_client.return_value = 'fantasy description'
        mock_insert_mission.return_value = True

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'], '"fantasy description"')

    @patch('modules.missions.insert_mission.app.validate_user')
    @patch('modules.missions.insert_mission.common.db_connection.get_secrets')
    def test_get_secrets_openai_client_exception(self, mock_get_secrets, mock_validate_user):
        mock_get_secrets.return_value = {
            'username': 'admin',
            'password': 'admin',
            'engine': 'admin',
            'host': 'admin',
            'port': 'admin',
            'dbname': 'admin',
            'dbInstanceIdentifier': 'admin'
        }

        mock_validate_user.return_value = True

        with patch('modules.missions.insert_mission.common.openai_connection.get_secret',
                   side_effect=Exception('Error getting secret')):
            response = app.lambda_handler(EVENT, None)
            self.assertEqual(response['body'], '"Error getting secret"')

    @patch('modules.missions.insert_mission.common.openai_connection.get_secret')
    @patch('modules.missions.insert_mission.app.validate_user')
    def test_get_openai_client_exception(self, mock_validate_user, mock_openai_get_secret):
        mock_validate_user.return_value = True
        mock_openai_get_secret.return_value = {
            'OPENAI_KEY': 'admin'
        }

        with patch('modules.missions.insert_mission.common.openai_connection.get_openai_client',
                   side_effect=Exception('Error getting openai client')):
            response = app.lambda_handler(EVENT, None)
            self.assertEqual(response['body'], '"Error getting openai client"')

    @patch('modules.missions.insert_mission.app.validate_user')
    def test_get_validate_user_exception(self, mock_validate_user):
        mock_validate_user.side_effect = Exception('Error')

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'], json.dumps("Error"))

    @patch('modules.missions.insert_mission.app.get_db_connection')
    @patch('modules.missions.insert_mission.app.get_openai_client')
    @patch('modules.missions.insert_mission.app.validate_user')
    def test_insert_mission_success(self, mock_validate_user, mock_get_openai_client, mock_get_db_connection):
        mock_validate_user.return_value = True
        mock_get_openai_client.return_value = 'fantasy description'

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        response = app.lambda_handler(EVENT, None)
        self.assertEqual(response['body'], '"fantasy description"')


if __name__ == '__main__':
    unittest.main()
