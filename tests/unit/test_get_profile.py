from modules.profile.get_profile import app
from unittest import TestCase

EVENT = {
    'pathParameters': {
       'id_user': '41bb3510-c0a1-7093-8adf-af851d916edd'
    }
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))
