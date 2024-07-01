import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.delete_user_profile import app
from modules.users.delete_user_profile.common.httpStatusCodeError import HttpStatusCodeError


class TestDeleteUserProfile(unittest.TestCase):

    @staticmethod
    def print_response(response):
        print("Status Code:", response['statusCode'])

        if 'body' in response:
            body = json.loads(response['body'])
            print("Response Body:", body)
        else:
            print("No body found in response")

    """
    Test class for the lambda_handler function on the case is successful
    """

    @patch('modules.users.delete_user_profile.app.delete_user_profile')
    @patch('modules.users.delete_user_profile.app.validate_body')
    @patch('modules.users.delete_user_profile.app.delete_user_cognito')
    @patch('modules.users.delete_user_profile.app.get_secret')
    def test_lambda_handler(self, mock_get_secret, mock_delete_user_cognito, mock_validate_body, mock_delete_user_profile):
        mock_get_secret.return_value = {
            'USER_POOL_ID': 'mock_pool_id'
        }

        mock_validate_body.return_value = True
        mock_delete_user_cognito.return_value = True
        mock_delete_user_profile.return_value = True

        body_user_successfully = {
            'body': json.dumps({
                'id': 1,
                'username': 'testuser'
            })
        }
        response = app.lambda_handler(body_user_successfully, None)
        expected_response = {
            'statusCode': 200,
            'body': json.dumps(f'User with id {json.loads(body_user_successfully["body"])["id"]} deleted successfully')
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_user_successfully['body'])

    """
    Test class for the lambda_handler function on:
        - the case where the id is required
        - the case where the id must be a non-empty int
    """

    def test_id_user_is_missing(self):
        body_id_user_is_missing = {
            'body': json.dumps({})
        }
        response = app.lambda_handler(body_id_user_is_missing, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Id is required")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_id_user_is_missing['body'])

    def test_id_user_is_not_int(self):
        body_id_user_is_not_int = {
            'body': json.dumps({
                'id': 'not_an_int',
            })
        }
        response = app.lambda_handler(body_id_user_is_not_int, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Id must be a non-empty int")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_id_user_is_not_int['body'])









    def test_username_is_missing(self):
        body_username_is_missing = {
            'body': json.dumps({
                'id': 1,
            })
        }
        response = app.lambda_handler(body_username_is_missing, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Username is required")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_username_is_missing['body'])

    def test_username_is_not_string(self):
        body_username_is_not_string = {
            'body': json.dumps({
                'id': 1,
                'username': 12345,
            })
        }
        response = app.lambda_handler(body_username_is_not_string, None)
        expected_response = {
            'statusCode': 400,
            'body': json.dumps("Username must be a string")
        }

        self.assertEqual(response, expected_response)
        self.print_response(response)
        print("Request body:", body_username_is_not_string['body'])


if __name__ == '__main__':
    unittest.main()
