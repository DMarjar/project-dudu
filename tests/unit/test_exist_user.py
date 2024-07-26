import json
from modules.users.exist_user import app
from unittest import TestCase
import pytest

EVENT = {
    'body': json.dumps({
        'id_user': '11eb8500-4021-704c-672d-',
    })
}


class Test(TestCase):
    def test_lambda_handler(self):
        print(app.lambda_handler(EVENT, None))