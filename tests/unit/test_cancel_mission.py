from unittest import TestCase
from modules.missions.cancel_mission.app import lambda_handler


class Test(TestCase):
    def test_lambda_handler(self):
        event = {'id_user': '1', 'id_mission': '1'}
        context = None
        result = lambda_handler(event, context)
        self.assertEqual(result, {
            'statusCode': 200,
            'body': '"Mission has been banished by the Gods"'
        })