import hmac
import boto3
import hashlib
import json
import base64
from secrets_manager import get_secret_value


def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def get_secret():
    secret_name = "users_pool/client_secret"
    secret = get_secret_value(secret_name)
    return secret


def lambda_handler(event, context):
    client = boto3.client('cognito-idp')
    secret = get_secret()

    body = json.loads(event['body'])
    username = body['username']
    client_id = '4iid9n3o306aorf0imcs0dcplo'
    client_secret = secret['SECRET_CLIENT']

    try:
        user = client.admin_get_user(
            UserPoolId='us-east-2_bjlyJabGh',
            Username=username
        )

        email = next((attr['Value'] for attr in user['UserAttributes'] if attr['Name'] == 'email'), None)
        email_verified = next((attr['Value'] for attr in user['UserAttributes'] if attr['Name'] == 'email_verified'),
                              'false')
        user_status = user['UserStatus']

        if not email:
            return {
                'statusCode': 404,
                'body': json.dumps('User email not found.')
            }

        if email_verified != 'true':
            return {
                'statusCode': 400,
                'body': json.dumps('User email not verified.')
            }

        if user_status != 'CONFIRMED':
            return {
                'statusCode': 400,
                'body': json.dumps("User account hasn't been confirmed.")
            }

    except client.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps('User not found.')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred while checking user existence: ' + str(e))
        }

    try:
        secret_hash = get_secret_hash(email, client_id, client_secret)

        response = client.forgot_password(
            ClientId=client_id,
            Username=email,
            SecretHash=secret_hash
        )
        return {
            'statusCode': 200,
            'body': json.dumps(response['CodeDeliveryDetails'])
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred: ' + str(e))
        }
