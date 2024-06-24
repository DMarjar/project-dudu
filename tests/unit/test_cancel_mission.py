import json
import unittest
from unittest.mock import patch, MagicMock
from modules.missions.cancel_mission import app
from modules.missions.cancel_mission.common.httpStatusCodeError import HttpStatusCodeError


class TestCancelMission(unittest.TestCase):

    """
    Test class for the lambda_handler function
        on the case is successful
    """

    # Initialize the decorator patch to mock the cancel_mission, get_openai_client and validate_user functions

    @patch('modules.missions.cancel_mission.app.cancel_mission')
    @patch('modules.missions.cancel_mission.app.validate_user')
    @patch('modules.missions.cancel_mission.common.db_connection.get_secrets')
    def test_lambda_handler(self, mock_get_secrets, mock_validate_user, mock_cancel_mission):
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
        mock_cancel_mission.return_value = True

        body_mission_succesfully = {
            'body': json.dumps({
                'id_mission': 1,
                'id_user': 1
            })
        }
        self.assertEqual(app.lambda_handler(body_mission_succesfully, None),
                         {'statusCode': 200, 'body': '"Mission cancelled successfully"'})

    """
    Test class for the lambda_handler function
        on 
        -the case where the id_mission is not in the body
        -the case where the id_mission is None
        -the case where the id_mission is not int
    """

    def test_no_id_mission(self):
        body_no_id_mission = {
            'body': json.dumps({
                'id_user': 1
            })
        }

        self.assertEqual(app.lambda_handler(body_no_id_mission, None),
                         {'statusCode': 400, 'body': '"id_mission is required"'})

    def test_id_mission_is_none(self):
        body_id_mission_is_none = {
            'body': json.dumps({
                'id_mission': None,
                'id_user': 1
            })
        }

        self.assertEqual(app.lambda_handler(body_id_mission_is_none, None),
                         {'statusCode': 400, 'body': '"id_mission is required"'})

    def test_id_mission_is_not_int(self):
        body_id_mission_is_not_int = {
            'body': json.dumps({
                'id_mission': 'one',
                'id_user': 1
            })
        }

        self.assertEqual(app.lambda_handler(body_id_mission_is_not_int, None),
                         {'statusCode': 400, 'body': '"id_mission must be an integer"'})

    """
    Test class for the lambda_handler function
        on
        -the case where the id_user is not in the body
        -the case where the id_user is None
        -the case where the id_user is not int
    """

    def test_no_id_user(self):
        body_no_id_user = {
            'body': json.dumps({
                'id_mission': 1
            })
        }

        self.assertEqual(app.lambda_handler(body_no_id_user, None),
                         {'statusCode': 400, 'body': '"id_user is required"'})

    def test_id_user_is_none(self):
        body_id_user_is_none = {
            'body': json.dumps({
                'id_mission': 1,
                'id_user': None
            })
        }

        self.assertEqual(app.lambda_handler(body_id_user_is_none, None),
                         {'statusCode': 400, 'body': '"id_user is required"'})

    def test_id_user_is_not_int(self):
        body_id_user_is_not_int = {
            'body': json.dumps({
                'id_mission': 1,
                'id_user': 'one'
            })
        }

        self.assertEqual(app.lambda_handler(body_id_user_is_not_int, None),
                         {'statusCode': 400, 'body': '"id_user must be an integer"'})

    """
    Test class for the validate_user function
        - when user exists
        - when user does not exist
        - when there is a user internal server error
    """

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_validate_user_exists(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{'id_user': 1}]
        try:
            app.validate_user(1)
            response = {'statusCode': 200, 'body': '"User validated successfully"'}
        except HttpStatusCodeError as e:
            response = {'statusCode': e.status_code, 'body': json.dumps(e.message)}

        self.assertEqual(response, {'statusCode': 200, 'body': '"User validated successfully"'})
    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_validate_user_not_exists(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        try:
            app.validate_user(1)
            response = {'statusCode': 200, 'body': '"User validated successfully"'}
        except HttpStatusCodeError as e:
            response = {'statusCode': e.status_code, 'body': json.dumps(e.message)}

        self.assertEqual(response, {'statusCode': 404, 'body': '"User not found"'})

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_validate_user_internal_server_error(self, mock_get_db_connection):
        mock_get_db_connection.side_effect = Exception("Database connection error")

        try:
            app.validate_user(1)
            response = {'statusCode': 200, 'body': '"User validated successfully"'}
        except Exception as e:
            response = {'statusCode': 500, 'body': json.dumps("Internal server error")}

        self.assertEqual(response, {'statusCode': 500, 'body': '"Internal server error"'})

    """
    Test class for the cancel_mission function
        - when mission is cancelled successfully
        - when mission not found or user unauthorized to cancel
        - when there is a mission internal server error
    """
    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_cancel_mission_successful(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.rowcount = 1

        try:
            app.cancel_mission(1, 1)
            response = {'statusCode': 200, 'body': '"Mission cancelled successfully"'}
        except HttpStatusCodeError as e:
            response = {'statusCode': e.status_code, 'body': json.dumps(e.message)}

        self.assertEqual(response, {'statusCode': 200, 'body': '"Mission cancelled successfully"'})

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_cancel_mission_not_found_or_unauthorized(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.rowcount = 0

        try:
            app.cancel_mission(1, 1)
            response = {'statusCode': 200, 'body': '"Mission cancelled successfully"'}
        except HttpStatusCodeError as e:
            response = {'statusCode': e.status_code, 'body': json.dumps(e.message)}

        self.assertEqual(response, {'statusCode': 404, 'body': '"Mission not found or user unauthorized to cancel"'})

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_cancel_mission_internal_server_error(self, mock_get_db_connection):
        mock_get_db_connection.side_effect = Exception("Database connection error")

        try:
            app.cancel_mission(1, 1)
            response = {'statusCode': 200, 'body': '"Mission cancelled successfully"'}
        except Exception as e:
            response = {'statusCode': 500, 'body': json.dumps("Internal server error")}

        self.assertEqual(response, {'statusCode': 500, 'body': '"Internal server error"'})


if __name__ == '__main__':
    unittest.main()