import unittest
import json
from modules.missions.update_mission import app

class TestUpdateMissionLambda(unittest.TestCase):
    def test_lambda_handler(self):
        event = {
            "body": json.dumps({
                "id_task": 1,
                "status": "completed"
            })
        }
        context = {}
        response = app.lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'Mission 1 completed successfully')

    def test_lambda_handler_with_exception(self):
        event = {
            "body": "invalid json"  # This will cause json.loads to throw an exception
        }
        context = {}
        response = app.lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertTrue("An error occurred while completing the mission" in body['message'])

