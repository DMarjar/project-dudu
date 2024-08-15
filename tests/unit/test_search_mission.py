import json
from unittest import TestCase
from unittest.mock import patch
from modules.missions.search_mission import app
from modules.missions.search_mission.common.httpStatusCodeError import HttpStatusCodeError


class MockCursor:
    def __init__(self, fetchall_return_value, fetchone_return_value=None):
        self.fetchall_return_value = fetchall_return_value
        self.fetchone_return_value = fetchone_return_value

    def execute(self, query, values):
        # Execute query
        pass

    def fetchall(self):
        return self.fetchall_return_value

    def fetchone(self):
        return self.fetchone_return_value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close cursor
        pass


class MockConnection:
    def __init__(self, cursor_return_value):
        self.cursor_return_value = cursor_return_value

    def cursor(self, *args, **kwargs):
        return self.cursor_return_value

    def close(self):
        # Close connection
        pass


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
                'order_by': 'due_date',
                'order': 'ASC',
                'status': 'pending',
                'page': 1,
                'limit': 6
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
                'status': 'pending',
            }
        ], 1
        mock_validate_user.return_value = True

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], json.dumps(
            {
                'missions': [
                    {
                        'id_mission': 1,
                        'original_description': 'original_description',
                        'fantasy_description': 'fantasy_description',
                        'id_user': 1,
                        'creation_date': '2022-01-01',
                        'status': 'pending',
                    }
                ],
                'total': 1
            }
        ))

    # Test lambda_handler without id_user in the body
    def test_lambda_handler_no_id_user(self):
        # Setup
        event = {
            'body': json.dumps({
                'search_query': 'search_query',
                'order_by': 'due_date',
                'order': 'ASC',
                'status': 'pending',
                'page': 1,
                'limit': 6
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
                'order_by': 'due_date',
                'order': 'ASC',
                'status': 'pending',
                'page': 1,
                'limit': 6
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
                'order': 'ASC',
                'status': 'pending',
                'page': 1,
                'limit': 6
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
                'order_by': 'due_date',
                'status': 'pending',
                'page': 1,
                'limit': 6
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
                'order_by': 'due_date',
                'order': 'ASC',
                'page': 1,
                'limit': 6
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("status is required"))

    # Test lambda_handler without page in the body
    def test_lambda_handler_no_page(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'due_date',
                'order': 'ASC',
                'status': 'pending',
                'limit': 6
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("invalid page"))

    # Test lambda_handler without limit in the body
    def test_lambda_handler_no_limit(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'due_date',
                'order': 'ASC',
                'status': 'pending',
                'page': 1
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("invalid limit"))

    # Test lambda_handler with order_by as null in the body
    def test_lambda_handler_order_by_null(self):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': '',
                'order': 'ASC',
                'status': 'pending',
                'page': 1,
                'limit': 6
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
                'order_by': 'due_date',
                'order': '',
                'status': 'pending',
                'page': 1,
                'limit': 6
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
                'order_by': 'due_date',
                'order': 'ASC',
                'status': '',
                'page': 1,
                'limit': 6
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
                'order_by': 'due_date',
                'order': 'ASC',
                'status': 'invalid',
                'page': 1,
                'limit': 6
            })
        }

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps("Invalid status"))

        # Test lambda_handler with Exception

    @patch("modules.missions.search_mission.app.validate_body")
    def test_lambda_handler_exception(self, mock_validate_body):
        # Setup
        event = {
            'body': json.dumps({
                'id_user': 1,
                'search_query': 'search_query',
                'order_by': 'due_date',
                'order': 'ASC',
                'status': 'pending',
                'page': 1,
                'limit': 6
            })
        }

        # Mock exception
        mock_validate_body.side_effect = HttpStatusCodeError(500, 'Server timeout')

        # Call
        response = app.lambda_handler(event, None)

        # Assert
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], json.dumps("Server timeout"))

    # Test validate_user with a successful response
    @patch("modules.missions.search_mission.app.get_db_connection")
    def test_validate_user(self, mock_get_db_connection):
        # Setup
        mock_cursor = MockCursor(fetchall_return_value=[{'id_user': 1}])
        mock_connection = MockConnection(cursor_return_value=mock_cursor)
        mock_get_db_connection.return_value = mock_connection

        # Call
        response = app.validate_user(1)

        # Assert
        self.assertTrue(response)

    # Test validate_user with user not found
    @patch("modules.missions.search_mission.app.get_db_connection")
    def test_validate_user_not_found(self, mock_get_db_connection):
        # Setup
        mock_cursor = MockCursor(fetchall_return_value=[])
        mock_connection = MockConnection(cursor_return_value=mock_cursor)
        mock_get_db_connection.return_value = mock_connection

        # Call and Assert
        with self.assertRaises(HttpStatusCodeError) as context:
            app.validate_user(1)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.message, 'User not found')

    # Test search_mission with a successful response
    @patch("modules.missions.search_mission.app.get_db_connection")
    def test_search_mission(self, mock_get_db_connection):
        # Setup
        fetchall_return_value = [
            {
                'id_mission': 1,
                'original_description': 'original_description',
                'fantasy_description': 'fantasy_description',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending',
            }
        ]

        fetchone_return_value = ({'total': 1})
        mock_cursor = MockCursor(
            fetchall_return_value=fetchall_return_value,
            fetchone_return_value=fetchone_return_value
        )
        mock_connection = MockConnection(cursor_return_value=mock_cursor)
        mock_get_db_connection.return_value = mock_connection

        mock_body = {
            'id_user': 1,
            'search_query': 'search_query',
            'order_by': 'due_date',
            'order': 'ASC',
            'status': 'pending',
            'page': 1,
            'limit': 6
        }

        # Call
        response, total = app.search_mission(mock_body)

        # Assert
        self.assertEqual(response, fetchall_return_value)
        self.assertEqual(total, 1)

    # Test search_mission with no missions found
    @patch("modules.missions.search_mission.app.get_db_connection")
    def test_search_mission_no_missions(self, mock_get_db_connection):
        # Setup
        fetchall_return_value = []
        fetchone_return_value = ({'total': 0})
        mock_cursor = MockCursor(
            fetchall_return_value=fetchall_return_value,
            fetchone_return_value=fetchone_return_value
        )
        mock_connection = MockConnection(cursor_return_value=mock_cursor)
        mock_get_db_connection.return_value = mock_connection

        mock_body = {
            'id_user': 1,
            'search_query': 'search_query',
            'order_by': 'due_date',
            'order': 'ASC',
            'status': 'pending',
            'page': 1,
            'limit': 6
        }

        # Call
        response, total = app.search_mission(mock_body)

        # Assert
        self.assertEqual(response, [])
        self.assertEqual(total, 0)