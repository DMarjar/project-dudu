import boto3
import json
from botocore.exceptions import ClientError
import hashlib
import hmac
import base64


def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def get_secret():
    secret_name = "users_pool/client_secret2"
    secret = get_secret_value(secret_name)
    return secret


def get_secret_value(secret_name, region_name="us-east-2"):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
