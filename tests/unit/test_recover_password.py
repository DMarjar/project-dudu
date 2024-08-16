import base64
import hashlib
import hmac
import json
import unittest
from unittest.mock import patch, Mock
from botocore.exceptions import ClientError, NoCredentialsError
from modules.users.recover_password.app import lambda_handler, get_secret_hash
from modules.users.recover_password import app


class FakeSecretsManagerClient:
    def get_secret_value(self, SecretId):
        if SecretId == "users_pool/client_secret2":
            return {
                'SecretString': json.dumps({
                    'SECRET_CLIENT': 'fake_secret',
                    'ID_CLIENT': 'fake_client_id',
                    'USER_POOL_ID': 'fake_user_pool_id'
                })
            }
        else:
            raise ClientError(
                {"Error": {"Code": "ResourceNotFoundException"}},
                "get_secret_value"
            )


class FakeCognitoIdpClient:

    def admin_get_user(self, UserPoolId, Username):
        if UserPoolId != 'fake_user_pool_id':
            raise ClientError(
                {"Error": {"Code": "InvalidParameterException"}},
                "admin_get_user"
            )
        if Username == 'testuser':
            return {
                'UserAttributes': [{'Name': 'email_verified', 'Value': 'true'},
                                   {'Name': 'email', 'Value': 'test@example.com'},
                                   {'Name': 'user_status', 'Value': 'true'}],
                'UserStatus': 'CONFIRMED'
            }
        else:
            raise ClientError(
                {"Error": {"Code": "UserNotFoundException"}},
                "admin_get_user"
            )

    def forgot_password(self, **kwargs):
        return {'CodeDeliveryDetails': {'Destination': 'test@example.com', 'DeliveryMedium': 'EMAIL',
                                        'AttributeName': 'email'}}


class FakeSession:
    def client(self, service_name, region_name=None):
        if service_name == 'secretsmanager' and region_name == 'us-east-2':
            return FakeSecretsManagerClient()
        elif service_name == 'cognito-idp' and region_name == 'us-east-2':
            return FakeCognitoIdpClient()
        else:
            raise ValueError("Unsupported service or region")


class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        self.patcher_boto_session = patch('boto3.session.Session', return_value=FakeSession())
        self.mock_boto_session = self.patcher_boto_session.start()

    def tearDown(self):
        self.patcher_boto_session.stop()

    def test_username_not_in_body(self):
        event = {
            'body': json.dumps({
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"(400, \'Username is required\')"')

    def test_get_secret_hash(self):
        username = 'testuser'
        client_id = 'clientid123'
        client_secret = 'secretkey'
        message = username + client_id
        dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        expected_result = base64.b64encode(dig).decode()
        result = get_secret_hash(username, client_id, client_secret)
        self.assertEqual(result, expected_result)

    def test_username_is_not_str(self):
        event = {
            'body': json.dumps({
                'username': 212,
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"(400, \'Username must be a string\')"')

    def test_username_is_none(self):
        event = {
            'body': json.dumps({
                'username': None
            })
        }
        response = app.lambda_handler(event, None)
        self.assertEqual(response['body'], '"(400, \'Username is required\')"')

    @patch('modules.users.recover_password.app.boto3.client')
    def test_get_secrets_client_error(self, mock_boto_client):
        mock_client_instance = mock_boto_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'get_secret_value'
        )
        with self.assertRaises(ClientError) as context:
            mock_client_instance.get_secret_value('some_secret_id')
        self.assertEqual(context.exception.response['Error']['Code'], 'ResourceNotFoundException')

    def test_email_need_verification(self):
        with patch('modules.users.recover_password.app.boto3.client',
                   side_effect=lambda service_name, region_name=None: FakeSession().client(service_name, region_name)):
            event = {
                'body': json.dumps({'username': 'testuser'})
            }
            context = {}
            response = lambda_handler(event, context)
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']),
                             "(200, 'MUST CHANGE TEMPORARY PASSWORD BECAUSE OF EMAIL VERIFICATION')")

    def test_get_secret_no_credentials_error(self):
        with patch('boto3.session.Session.client', return_value=FakeSecretsManagerClient()):
            with patch.object(FakeSecretsManagerClient, 'get_secret_value', side_effect=NoCredentialsError):
                event = {
                    'body': json.dumps({'username': 'testuser'})
                }
                context = {}
                response = lambda_handler(event, context)
                self.assertEqual(response['statusCode'], 500)
                self.assertIn('Error getting secret ->', response['body'])

    def test_get_secret_client_error(self):
        with patch('boto3.session.Session.client', return_value=FakeSecretsManagerClient()):
            with patch.object(FakeSecretsManagerClient, 'get_secret_value', side_effect=ClientError(
                    {'Error': {'Code': 'ResourceNotFoundException'}},
                    'get_secret_value')):
                event = {
                    'body': json.dumps({'username': 'testuser'})
                }
                context = {}
                response = lambda_handler(event, context)
                self.assertEqual(response['statusCode'], 500)
                self.assertIn('Error getting secret ->', response['body'])

    @patch('modules.users.recover_password.app.boto3.client')
    @patch('modules.users.recover_password.app.get_secret')
    @patch('modules.users.recover_password.app.verify_user')
    @patch('modules.users.recover_password.app.validate_body')
    def test_successful_password_reset(self, mock_validate_body, mock_verify_user, mock_get_secret, mock_boto_client):
        mock_validate_body.return_value = None
        mock_get_secret.return_value = {
            'ID_CLIENT': 'fake_client_id',
            'SECRET_CLIENT': 'fake_secret'
        }
        mock_verify_user.return_value = None
        mock_client = Mock()
        mock_client.forgot_password.return_value = {
            'CodeDeliveryDetails': {
                'Destination': 'test@example.com',
                'DeliveryMedium': 'EMAIL',
                'AttributeName': 'email'
            }
        }
        mock_boto_client.return_value = mock_client

        event = {
            'body': json.dumps({
                'username': 'Gislane',
                'confirmation_code': "813985",
                'password': '20213Tn105',
                'confirm_new_password': '20213Tn105!'
            })
        }
        context = {}
        headers = {'Access-Control-Allow-Headers': '*',
                   'Access-Control-Allow-Methods': 'OPTIONS,POST',
                   'Access-Control-Allow-Origin': '*'}
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(
            json.loads(response['body']),
            'A code to reset your password was sent to your email'
        )
        self.assertEqual(response['headers'], headers)


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
