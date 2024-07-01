import json
from unittest import TestCase
from unittest.mock import patch, MagicMock
from modules.missions.search_mission import app
from modules.missions.search_mission.common.httpStatusCodeError import HttpStatusCodeError


class TestSearchMissions(TestCase):
    # Test lambda_handler with a successful response
    @patch("modules.missions.search_mission.app.validate_user")
    @patch("modules.missions.search_mission.app.search_mission")
    def test_lambda_handler(self, mock_search_mission, mock_validate_user):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'order_by',
                'order': 'order',
                'status': 'pending'
            })
        }

        # Mock missions found dictionary
        mock_search_mission.return_value = [
            {
                'id_mission': 1,
                'original_description': 'original_description',
                'fantasy_description': 'fantasy_description',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            }
        ]
        mock_validate_user.return_value = True

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], json.dumps([
            {
                'id_mission': 1,
                'original_description': 'original_description',
                'fantasy_description': 'fantasy_description',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            }
        ]))

    # Test lambda_handler without id_user in the body
    def test_lambda_handler_no_id_user(self):
        # Setup
        event = {
            'body': json.dumps({
                'search_query': 'search_query',
                'order_by': 'order_by',
                'order': 'order',
                'status': 'pending'
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("id_user is required"))

    # Test lambda_handler without search_query in the body
    def test_lambda_handler_no_search_query(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'order_by': 'order_by',
                'order': 'order',
                'status': 'pending'
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("search_query is required"))

    # Test lambda_handler withouth order_by in the body
    def test_lambda_handler_no_order_by(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order': 'order',
                'status': 'pending'
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("order_by is required"))

    # Test lambda_handler without order in the body
    def test_lambda_handler_no_order(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'order_by',
                'status': 'pending'
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("order is required"))

    # Test lambda_handler without status in the body
    def test_lambda_handler_no_status(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'order_by',
                'order': 'order'
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("status is required"))

    # Test lambda_handler with order_by as null in the body
    def test_lambda_handler_order_by_null(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': '',
                'order': 'order',
                'status': 'pending'
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("order_by cannot be null"))

    # Test lambda_handler with order as null in the body
    def test_lambda_handler_order_null(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'order_by',
                'order': '',
                'status': 'pending'
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("order cannot be null"))

    # Test lambda_handler with status as null in the body
    def test_lambda_handler_status_null(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'order_by',
                'order': 'order',
                'status': ''
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("status cannot be null"))

    # Test lambda_handler with invalid status in the body
    def test_lambda_handler_invalid_status(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'order_by',
                'order': 'order',
                'status': 'invalid'
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("Invalid status"))

    # Test lambda_handler with Exception
    @patch("modules.missions.search_mission.app.validate_user")
    @patch("modules.missions.search_mission.app.search_mission")
    def test_lambda_handler_exception(self, mock_search_mission, mock_validate_user):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'order_by',
                'order': 'order',
                'status': 'pending'
            })
        }

        # Mock exception
        mock_search_mission.side_effect = Exception("Server timeout")

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], json.dumps("Server timeout"))

    # Test validate_user with a successful response
    @patch("modules.missions.search_mission.app.get_db_connection")
    def test_validate_user(self, mock_get_db_connection):
        # Setup
        connection = MagicMock()
        mock_get_db_connection.return_value = connection
        mock_cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                'id_user': 1
            }
        ]

        # Call
        response = app.validate_user(1)

        # Assert
        self.assertTrue(response)

    # Test validate_user with user not found
    @patch("modules.missions.search_mission.app.get_db_connection")
    def test_validate_user_not_found(self, mock_get_db_connection):
        # Setup
        connection = MagicMock()
        mock_get_db_connection.return_value = connection
        mock_cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        # Call and Assert
        with self.assertRaises(HttpStatusCodeError) as context:
            app.validate_user(1)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.message, 'User not found')

    # Test search_mission with a successful response
    @patch("modules.missions.search_mission.app.get_db_connection")
    def test_search_mission(self, mock_get_db_connection):
        # Setup
        connection = MagicMock()
        mock_get_db_connection.return_value = connection
        mock_cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_body = {
            'id_user': 1,
            'search_query': 'search_query',
            'order_by': 'order_by',
            'order': 'order',
            'status': 'pending'
        }

        # Mock missions found dictionary
        mock_cursor.fetchall.return_value = [
            {
                'id_mission': 1,
                'original_description': 'original_description',
                'fantasy_description': 'fantasy_description',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            }
        ]

        # Call
        response = app.search_mission(mock_body)

        # Assert
        self.assertEqual(response, [
            {
                'id_mission': 1,
                'original_description': 'original_description',
                'fantasy_description': 'fantasy_description',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            }
        ])
