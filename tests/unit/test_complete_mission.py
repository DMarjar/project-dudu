import json
import unittest
from unittest.mock import patch, MagicMock
from modules.missions.complete_mission.app import lambda_handler


# Evento de prueba
EVENT = {
    'body': json.dumps({
        'id_mission': 1,
        'id_user': 1
    })
}


class TestCompleteMission(unittest.TestCase):
    """
    Test class for the lambda_handler function
    """
    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_get_db_connection = patch('modules.missions.complete_mission.app.get_db_connection').start()
        self.mock_get_db_connection.return_value = self.mock_connection

    def tearDown(self):
        patch.stopall()

    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_lambda_handler_success(self, mock_get_db_connection):
        # Simulamos una conexión a la base de datos y cursor
        mock_get_db_connection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor

        # Simulamos el fetch de los datos del usuario
        self.mock_cursor.fetchone.return_value = (50, 100, 2)

        response = lambda_handler(EVENT, None)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn("Mission 1 completed successfully and XP updated", json.loads(response['body'])['message'])

        # Verificamos que el cursor y la conexión se usaron correctamente
        self.mock_cursor.execute.assert_any_call(
            "SELECT current_xp, xp_limit, level FROM users WHERE id_user = %s FOR UPDATE", (1,)
        )
        self.mock_cursor.execute.assert_any_call(
            "UPDATE missions SET status = 'completed' WHERE id_mission = %s", (1,)
        )
        self.mock_connection.commit.assert_called_once()
        self.mock_connection.close.assert_called_once()

    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_lambda_handler_failure(self, mock_get_db_connection):
        # Simulamos una conexión a la base de datos que lanza una excepción
        mock_get_db_connection.side_effect = Exception("Database error")

        response = lambda_handler(EVENT, None)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('An error occurred', json.loads(response['body'])['message'])

    @patch('modules.missions.complete_mission.app.update_mission_status')
    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_no_id_mission_or_user(self, mock_get_db_connection):
        self.mock_connection = MagicMock()
        mock_get_db_connection.return_value = self.mock_connection

        # Simulación de un cuerpo de solicitud sin id_mission y id_user
        body_no_ids = {
            'body': json.dumps({})
        }

        response = lambda_handler(body_no_ids, None)
        self.assertEqual(response['statusCode'], 402)
        self.assertIn('Bad request: id of mission and user is required', response['body'])

    @patch('modules.missions.complete_mission.app.update_mission_status')
    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_id_mission_is_none(self, mock_get_db_connection):
        self.mock_connection = MagicMock()
        mock_get_db_connection.return_value = self.mock_connection

        # Simulación de un cuerpo de solicitud con id_mission como None
        body_id_mission_is_none = {
            'body': json.dumps({
                'id_mission': None,
                'id_user': 1
            })
        }

        response = lambda_handler(body_id_mission_is_none, None)

        self.assertEqual(response['statusCode'], 402)
        self.assertIn('Bad request: id of mission and user is required', json.loads(response['body'])['message'])

    @patch('modules.missions.complete_mission.app.update_mission_status')
    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_id_mission_is_not_integer(self, mock_get_db_connection):
        self.mock_connection = MagicMock()
        mock_get_db_connection.return_value = self.mock_connection

        body_id_mission_is_not_integer = {
            'body': json.dumps({
                'id_mission': "one",
                'id_user': 1
            })
        }

        response = lambda_handler(body_id_mission_is_not_integer, None)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Invalid mission or user ID', json.loads(response['body'])['message'])


if __name__ == '__main__':
    unittest.main()
