import base64
import hashlib
import hmac
import json
import re
import boto3

from .common.httpStatusCodeError import HttpStatusCodeError
from botocore.exceptions import ClientError, NoCredentialsError


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        validate_body(body)

        secrets = get_secret()

        response = set_password(body, secrets)

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'body': json.dumps(e.message)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps('Internal server error')

        }

    return response


def validate_body(body):
    """
    validate payload
    Args:
        body: payload
        - username: username
        - password: password
        - new_password: new password
    """
    # Validate password
    if 'password' not in body:
        raise HttpStatusCodeError(400, "Password is required")
    if not body['password']:
        raise HttpStatusCodeError(400, "Password is required")
    if body['password'] is None:
        raise HttpStatusCodeError(400, "Password is required")
    if not isinstance(body['password'], str):
        raise HttpStatusCodeError(400, "Password must be a string")

    # Validate username
    if 'username' not in body:
        raise HttpStatusCodeError(400, "Username is required")
    if not body['username']:
        raise HttpStatusCodeError(400, "Username is required")
    if body['username'] is None:
        raise HttpStatusCodeError(400, "Username is required")
    if not isinstance(body['username'], str):
        raise HttpStatusCodeError(400, "Username must be a string")

    # Validate new password
    if 'new_password' not in body:
        raise HttpStatusCodeError(400, "New password is required")
    if not body['new_password']:
        raise HttpStatusCodeError(400, "New password is required")
    if body['new_password'] is None:
        raise HttpStatusCodeError(400, "New password is required")
    if not isinstance(body['new_password'], str):
        raise HttpStatusCodeError(400, "New password must be a string")
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', body['new_password']):
        raise HttpStatusCodeError(400, "New password must contain at least 8 characters, one uppercase, one lowercase, "
                                       "one number and one special character")

    return True


def get_secret():
    secret_name = "users_pool/client_secret"
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


def set_password(body, secrets):
    try:
        client = boto3.client('cognito-idp', region_name='us-east-2')

        user_pool_id = secrets['USER_POOL_ID']
        client_id = secrets['ID_CLIENT']
        client_secret = secrets['SECRET_CLIENT']
        secret_hash = get_secret_hash(body['username'], client_id, client_secret)

        # Verificar si el usuario requiere cambiar la contraseña
        data_user = client.admin_initiate_auth(
            UserPoolId=secrets['USER_POOL_ID'],
            ClientId=client_id,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': body['username'],
                'PASSWORD': body['password'],
                'SECRET_HASH': secret_hash
            }
        )

        if data_user['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            # Cambiar la contraseña
            client.respond_to_auth_challenge(
                ClientId=client_id,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=data_user['Session'],
                ChallengeResponses={
                    'USERNAME': body['username'],
                    'NEW_PASSWORD': body['new_password'],
                    'SECRET_HASH': secret_hash,
                    'userAttributes.nickname': body.get('nickname', 'defaultNickname'),
                    'user_status': 'CONFIRMED',
                }
            )

            # Actualizar el atributo email_verified
            client.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=body['username'],
                UserAttributes=[
                    {
                        'Name': 'email_verified',
                        'Value': 'true'
                    }
                ]
            )

            # Iniciar sesion una vez que se actualizo la contraseña
            tokens = client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': body['username'],
                    'PASSWORD': body['new_password'],
                    'SECRET_HASH': secret_hash
                },
                ClientId=client_id
            )

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'id_token': tokens['AuthenticationResult']['IdToken'],
                    'access_token': tokens['AuthenticationResult']['AccessToken'],
                    'refresh_token': tokens['AuthenticationResult']['RefreshToken'],
                    'username': body['username']
                })
            }


    except Exception as e:
        raise HttpStatusCodeError(500, "Error creating cognito client")


def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()
