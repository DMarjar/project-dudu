import json
import unittest
from unittest.mock import patch, MagicMock
from modules.users.register_alexa_user import app


FAKE_SECRET = {'SecretString': json.dumps({
    'SECRET_CLIENT': 'client',
    'ID_CLIENT': 'id',
    'USER_POOL_ID': 'pool'
})}


# To test_lambda_handler
class FakeSessionTestLambdaHandler:
    """
    FakeSession class to mock boto3 session
    """

    def __init__(self, *args, **kwargs):
        pass

    def client(self, *args, **kwargs):
        return FakeBoto3ClientTestLambdaHandler()


class FakeBoto3ClientTestLambdaHandler:
    def __init__(self, *args, **kwargs):
        pass

    def get_secret_value(self, *args, **kwargs):
        return FAKE_SECRET


class Test(unittest.TestCase):
    @patch('modules.users.register_alexa_user.app.get_db_connection')
    def test_lambda_handler(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ['aprendiz de metodología magícaaa']

        event = {
            'body': json.dumps({
                'id_user': 'some-unique-id',
                'username': 'Atoferatofe'
            })
        }

        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], 'aprendiz de metodología magícaaa')

    @patch('modules.users.register_alexa_user.app.save_user_db')
    def test_save_user_db_exception(self, mock_save_user_db):
        mock_save_user_db.side_effect = Exception("Error inserting user")

        event = {
            'body': json.dumps({
                'id_user': 'some-unique-id-2',
                'username': 'Atoferatofe'
            })
        }

        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Error inserting user"')

    @patch('modules.users.register_alexa_user.app.give_basic_rewards')
    @patch('modules.users.register_alexa_user.app.get_db_connection')
    def test_give_basic_rewards_exception(self, mock_get_db_connection, mock_give_basic_rewards):
        mock_connection = MagicMock()
        mock_get_db_connection.return_value = mock_connection

        mock_give_basic_rewards.side_effect = Exception("Error giving basic rewards")

        event = {
            'body': json.dumps({
                'id_user': 'some-unique-id-3',
                'username': 'Atoferatofe'
            })
        }

        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Error giving basic rewards"')

    """
    test_validate_body
        raise exceptions on all cases
    """

    def test_username_not_in_body(self):
        event = {
            'body': json.dumps({
                'id_user': 'some-unique-id'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"username is required"')

    def test_username_is_none(self):
        event = {
            'body': json.dumps({
                'username': None,
                'id_user': 'some-unique-id'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"username is required"')

    def test_username_is_not_str(self):
        event = {
            'body': json.dumps({
                'username': 123,
                'id_user': 'some-unique-id'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"username must be a string"')

    def test_id_user_not_in_body(self):
        event = {
            'body': json.dumps({
                'username': 'Atoferatofe'
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"id_user is required"')

    def test_id_user_is_none(self):
        event = {
            'body': json.dumps({
                'username': 'Atoferatofe',
                'id_user': None
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], '"id_user is required"')

    @patch('modules.users.register_alexa_user.app.get_db_connection')
    def test_get_first_title_exception(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = Exception('Error getting first title')

        event = {
            'body': json.dumps({
                'id_user': 'some-unique-id-4',
                'username': 'Atoferatofe'
            })
        }

        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"Error getting first title"')


if __name__ == '__main__':
    unittest.main()
