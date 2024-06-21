import json
import unittest
from unittest.mock import patch, MagicMock
from modules.missions.insert_mission import app

EVENT = {
    'body': json.dumps({
        'original_description': 'test',
        'id_user': 1,
        'creation_date': '2022-01-01',
        'status': 'pending'
    })
}


class Test(unittest.TestCase):
    """
    Test class for the lambda_handler function
        on the case is successful
    """

    # Initialize the decorator patch to mock the get_secrets and get_db_connection functions
    @patch('modules.missions.insert_mission.app.insert_mission')
    @patch('modules.missions.insert_mission.app.get_openai_client')
    @patch('modules.missions.insert_mission.app.validate_user')
    @patch('modules.missions.insert_mission.common.db_connection.get_secrets')
    def test_lambda_handler(self, mock_get_secrets, mock_validate_user, mock_get_openai_client, mock_insert_mission):
        # Initialize the mock objects
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

        self.assertEqual(app.lambda_handler(EVENT, None),
                         {'statusCode': 200, 'body': '"Mission inserted successfully"'})

    """
    Test class for the lambda_handler function
        on 
        -the case where the original description is not in the body
        -the case where the original description is None
        -the case where the original description is not string
        -the case where the original description is an empty string
    """

    def test_no_original_description(self):
        body_no_original_description = {
            'body': json.dumps({
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_no_original_description, None),
                         {'statusCode': 400, 'body': '"original_description is required"'})

    def test_original_description_is_none(self):
        body_original_description_is_none = {
            'body': json.dumps({
                'original_description': None,
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_original_description_is_none, None),
                         {'statusCode': 400, 'body': '"original_description is required"'})

    def test_original_description_is_not_string(self):
        body_original_description_is_not_string = {
            'body': json.dumps({
                'original_description': 123,
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_original_description_is_not_string, None),
                         {'statusCode': 400, 'body': '"original_description must be a string"'})

    def test_original_description_is_empty_string(self):
        body_original_description_is_empty_string = {
            'body': json.dumps({
                'original_description': '',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_original_description_is_empty_string, None),
                         {'statusCode': 400, 'body': '"original_description cannot be empty"'})

    """
    Test class for the lambda_handler function
        on
        -the case where the id_user is not in the body
        -the case where the id_user is None
    """

    def test_no_id_user(self):
        body_no_id_user = {
            'body': json.dumps({
                'original_description': 'test',
                'creation_date': '2022-01-01',
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_no_id_user, None),
                         {'statusCode': 400, 'body': '"id_user is required"'})

    def test_id_user_is_none(self):
        body_id_user_is_none = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': None,
                'creation_date': '2022-01-01',
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_id_user_is_none, None),
                         {'statusCode': 400, 'body': '"id_user is required"'})

    """
    Test class for the lambda_handler function
        on
        -the case where the creation_date is not in the body
        -the case where the creation_date is None
        -the case where the creation_date is not in the correct format
    """

    def test_no_creation_date(self):
        body_no_creation_date = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_no_creation_date, None),
                         {'statusCode': 400, 'body': '"creation_date is required"'})

    def test_creation_date_is_none(self):
        body_creation_date_is_none = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': None,
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_creation_date_is_none, None),
                         {'statusCode': 400, 'body': '"creation_date is required"'})

    def test_creation_date_is_incorrect_format(self):
        body_creation_date_is_incorrect_format = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '01-01-2022',
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(body_creation_date_is_incorrect_format, None),
                         {'statusCode': 400, 'body': '"Incorrect creation_date format, should be YYYY-MM-DD"'})

    """ 
    Test class for the lambda_handler function
        on
        -the case where the status is not in the body
        -the case where the status is None
        -the case where the status is not in the correct format
    
    correct format: ['pending', 'completed', 'cancelled', 'in_progress']
    """

    def test_no_status(self):
        body_no_status = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01'
            })
        }

        self.assertEqual(app.lambda_handler(body_no_status, None),
                         {'statusCode': 400, 'body': '"status is required"'})

    def test_status_is_none(self):
        body_status_is_none = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': None
            })
        }

        self.assertEqual(app.lambda_handler(body_status_is_none, None),
                         {'statusCode': 400, 'body': '"status is required"'})

    def test_status_is_invalid(self):
        body_status_is_invalid = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'invalid'
            })
        }

        self.assertEqual(app.lambda_handler(body_status_is_invalid, None),
                         {'statusCode': 400, 'body': '"Invalid status"'})

    """
    Test class for the lambda_handler function
        on the case where the get_secrets function on the db_connection module raises an exception
    """

    def test_get_secrets_exception(self):
        self.assertEqual(app.lambda_handler(EVENT, None),
                         {'statusCode': 500, 'body': '"Error getting secret"'})

    """
    Test class for the lambda_handler function
        on the case connection to the database fails
    """

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

        self.assertEqual(app.lambda_handler(EVENT, None),
                         {'statusCode': 500, 'body': '"Error connecting to database"'})

    """
    Test class for the lambda_handler function
        on the case where the get_secret function on the openai_connection module raises an exception
    """

    @patch('modules.missions.insert_mission.app.validate_user')
    @patch('modules.missions.insert_mission.common.db_connection.get_secrets')
    def test_get_openai_client_exception(self, mock_get_secrets, mock_validate_user):
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

        self.assertEqual(app.lambda_handler(EVENT, None),
                            {'statusCode': 500, 'body': '"Error getting secret"'})



if __name__ == '__main__':
    unittest.main()