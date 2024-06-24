import json
from unittest import TestCase
from unittest.mock import patch
from modules.missions.get_all_missions import app
from modules.missions.get_all_missions.common import db_connection


class TestGetAllMissions(TestCase):
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

    @patch('modules.missions.get_all_missions.app.get_all_missions')
    def test_no_missions(self, mock_get_all_missions):
        mock_get_all_missions.return_value = []
        self.assertEqual(app.lambda_handler(None, None),
                         {'statusCode': 204, 'body': json.dumps("No missions found")})

    @patch('modules.missions.get_all_missions.app.get_all_missions')
    def test_exception(self, mock_get_all_missions):
        mock_get_all_missions.side_effect = Exception("Server timeout error")
        self.assertEqual(app.lambda_handler(None, None),
                         {'statusCode': 500, 'body': json.dumps(
                             "An error occurred while getting the missions: "
                             "Server timeout error")})

    @patch('modules.missions.get_all_missions.common.db_connection.get_secrets')
    @patch('modules.missions.get_all_missions.common.db_connection.pymysql.connect')
    def test_get_db_connection(self, mock_connect, mock_get_secrets):
        mock_get_secrets.return_value = {
            'username': 'admin',
            'password': 'admin',
            'engine': 'admin',
            'host': 'admin',
            'port': 'admin',
            'dbname': 'admin',
            'dbInstanceIdentifier': 'admin'
        }

        db_connection.get_db_connection()
        mock_connect.assert_called_once_with(
            host='dududb.c7gis6w4srg8.us-east-2.rds.amazonaws.com',
            user='admin',
            password='admin',
            db='dududb'
        )

    @patch('modules.missions.get_all_missions.common.db_connection.boto3')
    def test_get_secrets(self, mock_boto3):
        mock_client = mock_boto3.session.Session().client
        mock_client.return_value.get_secret_value.return_value = {
            'SecretString': '{"username": "admin", "password": "admin"}'
        }

        self.assertEqual(db_connection.get_secrets(), {
            'username': 'admin',
            'password': 'admin'
        })
        mock_client.assert_called_once_with(
            service_name='secretsmanager',
            region_name='us-east-2'
        )
        mock_client.return_value.get_secret_value.assert_called_once_with(SecretId='dudu/db/connection')

    @patch('modules.missions.get_all_missions.common.db_connection.boto3')
    def test_get_secrets_exception(self, mock_boto3):
        mock_client = mock_boto3.session.Session().client
        mock_client.return_value.get_secret_value.side_effect = Exception("Server timeout error")

        with self.assertRaises(Exception) as context:
            db_connection.get_secrets()
        self.assertEqual(str(context.exception), "Server timeout error")
