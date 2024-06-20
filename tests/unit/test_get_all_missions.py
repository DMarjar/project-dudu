import json
from unittest import TestCase
from unittest.mock import patch
from modules.missions.get_all_missions import app


class Test(TestCase):
    @patch('modules.missions.get_all_missions.app.get_all_missions')
    @patch('modules.missions.get_all_missions.common.db_connection.get_secrets')
    def test_lambda_handler(self, mock_get_secrets, mock_get_all_missions):
        mock_get_secrets.return_value = {
            'username': 'admin',
            'password': 'admin',
            'engine': 'admin',
            'host': 'admin',
            'port': 'admin',
            'dbname': 'admin',
            'dbInstanceIdentifier': 'admin'
        }

        mock_get_all_missions.return_value = {
            'id_mission': 1,
            'original_description': 'test',
            'id_user': 1,
            'creation_date': '2022-01-01',
            'status': 'pending'
        }

        self.assertEqual(app.lambda_handler(None, None),
                         {'statusCode': 200, 'body': json.dumps({
                             'id_mission': 1,
                             'original_description': 'test',
                             'id_user': 1,
                             'creation_date': '2022-01-01',
                             'status': 'pending'
                         })})
