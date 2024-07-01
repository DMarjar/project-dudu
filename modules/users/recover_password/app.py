import boto3
import json
import hmac
import hashlib
import base64
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def get_secret():
    secret_name = "users_pool/client_secret"
    region_name = "us-east-2"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        logger.info(f"Attempting to retrieve secret '{secret_name}'...")
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    logger.info(f"Successfully retrieved secret '{secret_name}'.")

    return json.loads(secret)


def lambda_handler(event, context):
    client = boto3.client('cognito-idp')
    secret = get_secret()

    body = json.loads(event['body'])
    username = body['username']
    client_id = '4iid9n3o306aorf0imcs0dcplo'
    client_secret = secret['SECRET_CLIENT']

    secret_hash = get_secret_hash(username, client_id, client_secret)

    try:
        response = client.forgot_password(
            ClientId=client_id,
            Username=username,
            SecretHash=secret_hash
        )
        return {
            'statusCode': 200,
            'body': json.dumps('Password recovery initiated successfully.')
        }
    except client.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps('User not found.')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred: ' + str(e))
        }
