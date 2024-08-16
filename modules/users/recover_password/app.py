import boto3
import json
import base64
import hashlib
import hmac
from botocore.exceptions import ClientError, NoCredentialsError
from .common.httpStatusCodeError import HttpStatusCodeError


def lambda_handler(event, ___):
    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    }

    try:
        body = json.loads(event['body'])
        validate_body(body)

        secrets = get_secret()

        username = body['username']
        try:
            verify_user(username, secrets)
        except HttpStatusCodeError as e:
            if "User does not exist" in str(e):
                # Si el usuario no existe, asume que es un email e intenta obtener el username asociado
                username = get_username_from_email(username, secrets)
                verify_user(username, secrets)
            else:
                raise

        client = boto3.client('cognito-idp', region_name='us-east-2')
        client_id = secrets['ID_CLIENT']
        client_secret = secrets['SECRET_CLIENT']

        secret_hash = get_secret_hash(body['username'], client_id, client_secret)

        response = client.forgot_password(
            ClientId=client_id,
            Username=body['username'],
            SecretHash=secret_hash
        )

        response['headers'] = headers

        return {
            'statusCode': 200,
            'body': json.dumps(response['CodeDeliveryDetails']),
            'headers': headers
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred: ' + str(e)),
            'headers': headers
        }


def validate_body(body):
    """
    Validate payload
    Args:
        body (dict): Payload
        - username (str): User username
    """
    # Validate username
    if 'username' not in body:
        raise HttpStatusCodeError(400, "Username is required")
    if not body['username']:
        raise HttpStatusCodeError(400, "Username is required")
    if body['username'] is None:
        raise HttpStatusCodeError(400, "Username is required")
    if not isinstance(body['username'], str):
        raise HttpStatusCodeError(400, "Username must be a string")

    return True


def get_secret():
    secret_name = "users_pool/client_secret2"
    region_name = "us-east-2"

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
        raise HttpStatusCodeError(500, "Error getting secret -> " + str(e))
    except NoCredentialsError as e:
        raise HttpStatusCodeError(500, "Error getting secret -> " + str(e))

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


def verify_user(username, secrets):
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = secrets['USER_POOL_ID']

    try:
        user = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            raise HttpStatusCodeError(404, "User does not exist")
        else:
            raise

    email_verified = user['UserAttributes'][1]['Value']
    user_status = user['UserStatus']

    if str.lower(email_verified) != 'true':
        raise HttpStatusCodeError(200, "MUST CHANGE TEMPORARY PASSWORD")
    if user_status != 'CONFIRMED':
        raise HttpStatusCodeError(200, "MUST CHANGE TEMPORARY PASSWORD")

    return True


def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def get_username_from_email(email, secrets):
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = secrets['USER_POOL_ID']

    try:
        response = client.list_users(
            UserPoolId=user_pool_id,
            Filter=f'email = "{email}"'
        )
        if len(response['Users']) == 0:
            raise HttpStatusCodeError(404, "No user found with the provided email")

        return response['Users'][0]['Username']

    except ClientError as e:
        raise HttpStatusCodeError(500, "Error getting username from email -> " + str(e))
