import json
import unittest
from unittest.mock import patch, MagicMock
from modules.missions.complete_mission.app import lambda_handler


# Evento de prueba
EVENT = {
    'body': json.dumps({
        'id_mission': 1
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

        response = lambda_handler(EVENT, None)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['message'], "Mission 1 completed successfully")

        # Verificamos que el cursor y la conexión se usaron correctamente
        self.mock_cursor.execute.assert_called_once_with("UPDATE missions SET status = %s WHERE id_mission = %s",
                                                         ('completed', 1))
        self.mock_connection.commit.assert_called_once()
        self.mock_connection.close.assert_called_once()

    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_lambda_handler_failure(self, mock_get_db_connection):
        # Simulamos una conexión a la base de datos que lanza una excepción
        mock_get_db_connection.side_effect = Exception("Database error")

        response = lambda_handler(EVENT, None)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('An error occurred while completing the mission', json.loads(response['body'])['message'])

    @patch('modules.missions.complete_mission.app.update_mission_status')
    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_no_id_mission(self, mock_get_db_connection, mock_update_mission_status):
        self.mock_connection = MagicMock()
        mock_get_db_connection.return_value = self.mock_connection
        # Configura el mock para update_mission_status
        mock_update_mission_status.return_value = None
        # Simulación de un cuerpo de solicitud sin id_mission
        body_no_id_mission = {
            'body': json.dumps({})
        }
        # Simulación de la función lambda_handler
        response = lambda_handler(body_no_id_mission, None)
        # Comprobación de que la respuesta tiene el estado 400
        self.assertEqual(response['statusCode'], 400)
        # Comprobación de que el mensaje de error está presente en la respuesta
        self.assertIn('Bad request: Body is required', response['body'])

    @patch('modules.missions.complete_mission.app.update_mission_status')
    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_id_mission_is_none(self, mock_get_db_connection, mock_update_mission_status):
        self.mock_connection = MagicMock()
        mock_get_db_connection.return_value = self.mock_connection

        # Configura el mock para update_mission_status
        mock_update_mission_status.return_value = None

        # Simulación de un cuerpo de solicitud con id_mission como None
        body_id_mission_is_none = {
            'body': json.dumps({
                'id_mission': None
            })
        }

        # Simulación de la función lambda_handler
        response = lambda_handler(body_id_mission_is_none, None)

        # Comprobación de que la respuesta tiene el estado 400
        self.assertEqual(response['statusCode'], 402)
        # Comprobación de que el mensaje de error está presente en la respuesta
        self.assertIn('Bad request: id of mission is required', json.loads(response['body'])['message'])

    @patch('modules.missions.complete_mission.app.update_mission_status')
    @patch('modules.missions.complete_mission.app.get_db_connection')
    def test_id_mission_is_not_integer(self, mock_get_db_connection, mock_update_mission_status):
        self.mock_connection = MagicMock()
        mock_get_db_connection.return_value = self.mock_connection
        mock_update_mission_status.return_value = None

        body_id_mission_is_not_integer = {
            'body': json.dumps({
                'id_mission': "one"
            })
        }

        response = lambda_handler(body_id_mission_is_not_integer, None)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Mission not found', json.loads(response['body'])['message'])


if __name__ == '__main__':
    unittest.main()
