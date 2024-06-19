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

    # Initialize the decorator patch to mock the get_secrets and get_db_connection functions

    @patch('modules.missions.insert_mission.app.insert_mission')
    @patch('modules.missions.insert_mission.app.validate_user')
    @patch('modules.missions.insert_mission.common.db_connection.get_secrets')
    def test_lambda_handler(self,  mock_get_secrets, mock_validate_user, mock_get_openai_client, mock_insert_mission):
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


if __name__ == '__main__':
    unittest.main()
