from unittest import TestCase
from modules.missions.complete_mission.app import lambda_handler


class TestCompleteMission(TestCase):
    def test_lambda_handler(self):
        event = {
            'body': '{"id_mission": 1}'
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], '{"message": "Mission 1 completed successfully"}')