import json
import unittest
from unittest.mock import patch, MagicMock
from modules.missions.cancel_mission import app
from modules.missions.cancel_mission.app import validate_body, validate_user, cancel_mission, lambda_handler
from modules.missions.cancel_mission.common.httpStatusCodeError import HttpStatusCodeError


class TestCancelMission(unittest.TestCase):

    def test_validate_body_success(self):
        body = {'id_mission': 1, 'id_user': 1}
        self.assertTrue(validate_body(body))

    def test_validate_body_missing_id_mission(self):
        body = {'id_user': 1}
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.args, (400, "id_mission is required"))

    def test_validate_body_id_mission_none(self):
        body = {'id_mission': None, 'id_user': 1}
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.args, (400, "id_mission is required"))

    def test_validate_body_id_mission_not_int(self):
        body = {'id_mission': 'string', 'id_user': 1}
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.args, (400, "id_mission must be an integer"))

    def test_validate_body_missing_id_user(self):
        body = {'id_mission': 1}
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.args, (400, "id_user is required"))

    def test_validate_body_id_user_none(self):
        body = {'id_mission': 1, 'id_user': None}
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_body(body)
        self.assertEqual(context.exception.args, (400, "id_user is required"))

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_validate_user_success(self, mock_get_db_connection):
        def mock_cursor():
            class Cursor:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    pass

                def execute(self, sql, params):
                    pass

                def fetchall(self):
                    return [(1,)]

            return Cursor()

        mock_get_db_connection.return_value.cursor = mock_cursor
        id_user = 1
        self.assertTrue(validate_user(id_user))

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_validate_user_not_found(self, mock_get_db_connection):
        def mock_cursor():
            class Cursor:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    pass

                def execute(self, sql, params):
                    pass

                def fetchall(self):
                    return []
            return Cursor()

        mock_get_db_connection.return_value.cursor = mock_cursor
        id_user = 1
        with self.assertRaises(HttpStatusCodeError) as context:
            validate_user(id_user)
        self.assertEqual(context.exception.args, (404, "User not found"))

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_validate_user_db_error(self, mock_get_db_connection):
        def mock_cursor():
            class Cursor:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    pass

                def execute(self, sql, params):
                    raise Exception("DB Error")

                def fetchall(self):
                    pass

            return Cursor()

        mock_get_db_connection.return_value.cursor = mock_cursor
        id_user = 1
        with self.assertRaises(Exception) as context:
            validate_user(id_user)
        self.assertTrue('DB Error' in str(context.exception))


    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_cancel_mission_success(self, mock_get_db_connection):
        def mock_cursor():
            class Cursor:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    pass

                def execute(self, sql, params):
                    pass

                def fetchall(self):
                    pass

                def rowcount(self):
                    return 1  # Simula una actualización exitosa

            return Cursor()

        mock_get_db_connection.return_value.cursor = mock_cursor
        id_mission = 1
        id_user = 1
        self.assertTrue(cancel_mission(id_mission, id_user))

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_cancel_mission_db_error(self, mock_get_db_connection):
        def mock_cursor():
            class Cursor:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    pass

                def execute(self, sql, params):
                    raise Exception("DB Error")  # Simula un error en la base de datos

                def fetchall(self):
                    pass

                def rowcount(self):
                    pass

            return Cursor()

        mock_get_db_connection.return_value.cursor = mock_cursor
        id_mission = 1
        id_user = 1
        with self.assertRaises(Exception) as context:
            cancel_mission(id_mission, id_user)
        self.assertTrue('DB Error' in str(context.exception))

    @patch('modules.missions.cancel_mission.app.get_db_connection')
    def test_cancel_mission_not_found(self, mock_get_db_connection):
        # Simular el cursor
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0  # Simula que la misión no se encuentra

        # Simular la conexión y el cursor
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Configurar el mock de get_db_connection
        mock_get_db_connection.return_value = mock_connection

        id_mission = 1
        id_user = 1

        # Ejecutar la función y verificar la excepción
        with self.assertRaises(HttpStatusCodeError) as context:
            cancel_mission(id_mission, id_user)

        self.assertEqual(context.exception.args, (404, "Mission not found or user unauthorized to cancel"))


    @patch('modules.missions.cancel_mission.app.validate_body')
    @patch('modules.missions.cancel_mission.app.validate_user')
    @patch('modules.missions.cancel_mission.app.cancel_mission')
    def test_lambda_handler_success(self, mock_cancel_mission, mock_validate_user, mock_validate_body):
        # Configurar los mocks para que no lancen excepciones
        mock_validate_body.return_value = True
        mock_validate_user.return_value = True
        mock_cancel_mission.return_value = True

        # Crear un evento simulado
        event = {
            'body': '{"id_mission": 1, "id_user": 1}'
        }

        # Ejecutar la lambda handler
        response = lambda_handler(event, None)

        # Verificar que la respuesta es correcta
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Mission cancelled successfully', response['body'])

    @patch('modules.missions.cancel_mission.app.validate_body')
    @patch('modules.missions.cancel_mission.app.validate_user')
    @patch('modules.missions.cancel_mission.app.cancel_mission')
    def test_lambda_handler_http_error(self, mock_cancel_mission, mock_validate_user, mock_validate_body):
        # Configurar los mocks
        mock_validate_body.side_effect = HttpStatusCodeError(400, "Validation error")

        # Crear un evento simulado
        event = {
            'body': '{"id_mission": 1, "id_user": 1}'
        }

        # Ejecutar la lambda handler
        response = lambda_handler(event, None)

        # Verificar que la respuesta es correcta
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Validation error', response['body'])
if __name__ == '__main__':
    unittest.main()
