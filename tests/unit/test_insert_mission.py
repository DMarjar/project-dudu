import json
from modules.missions.insert_mission import app
from unittest import TestCase
import pytest


class Test(TestCase):
    def test_lambda_handler(self):
        event = {
            'body': json.dumps({
                'original_description': 'test',
                'id_user': 1,
                'creation_date': '2022-01-01',
                'status': 'pending'
            })
        }

        self.assertEqual(app.lambda_handler(event, None), {'statusCode': 200, 'body': '"Mission inserted successfully"'})