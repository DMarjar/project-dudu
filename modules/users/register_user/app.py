import json
import re
import string
import random

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from common.httpStatusCodeError import HttpStatusCodeError
from common.db_connection import get_db_connection

def lambda_handler(event, ___):
    try:
        body = json.loads(event['body'])

        validate_body(body)

        # Generate temporary password
        password = generate_temporary_password()
        body['password'] = password

        # Get secrets to save the user on AWS Cognito
        secrets = get_secret()

        # Save user on AWS Cognito
        id_user = save_user_cognito(body, secrets)

        # Save user on DB
        save_user_db(id_user, body['gender'])

        # Give basic rewards
        give_basic_rewards(id_user)

        response = {
            'statusCode': 200,
            'body': json.dumps("User registered successfully"),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
        }

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'body': json.dumps(e.message)
        }
    except Exception as e:
        error_message = str(e) if e is not None else "Unknown error"
        response = {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({"error": error_message}),
        }

    return response


def validate_body(body):
    """
    Validate payload
    Args:
        body (dict): Payload
        - email (str): User email
        - username (str): User username
        - gender (str): M or F

    """
    # Validate email
    if 'email' not in body:
        raise HttpStatusCodeError(400, "email is required")
    if body['email'] is None:
        raise HttpStatusCodeError(400, "email is required")
    if not isinstance(body['email'], str):
        raise HttpStatusCodeError(400, "email must be a string")
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', body['email']):
        raise HttpStatusCodeError(400, "Invalid email format")

    # Validate username
    if 'username' not in body:
        raise HttpStatusCodeError(400, "username is required")
    if body['username'] is None:
        raise HttpStatusCodeError(400, "username is required")
    if not isinstance(body['username'], str):
        raise HttpStatusCodeError(400, "username must be a string")
    if len(body['username']) < 3:
        raise HttpStatusCodeError(400, "username must be at least 3 characters long")
    if len(body['username']) > 20:
        raise HttpStatusCodeError(400, "username must be at most 20 characters long")

    # Validate gender
    if 'gender' not in body:
        raise HttpStatusCodeError(400, "gender is required")
    if body['gender'] is None:
        raise HttpStatusCodeError(400, "gender is required")
    if not body['gender'] in ['M', 'F']:
        raise HttpStatusCodeError(400, "invalid gender value, must be M or F")

    return True


def generate_temporary_password(length=12):
    """Genera una contraseña temporal segura"""
    special_characters = '^$*.[]{}()?:;-!@#%&/,><|_'
    characters = string.ascii_letters + string.digits + special_characters

    while True:
        # Genera una contraseña aleatoria
        password = ''.join(random.choice(characters) for _ in range(length))

        # Verifica los criterios
        has_digit = any(char.isdigit() for char in password)
        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_special = any(char in special_characters for char in password)

        if has_digit and has_upper and has_lower and has_special and len(password) >= 8:
            return password


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


def save_user_cognito(body, secrets):
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = secrets['USER_POOL_ID']

    response = client.admin_create_user(
        UserPoolId=user_pool_id,
        Username=body['username'],
        UserAttributes=[
            {
                'Name': 'email',
                'Value': body['email']
            }
        ],
        TemporaryPassword=body['password']
    )

    return response['User']['Attributes'][1]['Value']


def save_user_db(id_user, gender):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO users (id_user, gender) VALUES (%s, %s)"
            cursor.execute(sql, (id_user, gender))
        connection.commit()
    except Exception as e:
        raise HttpStatusCodeError(500, "Error inserting user")
    finally:
        connection.close()
    return True


def give_basic_rewards(id_user):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO user_rewards (id_user, id_reward) VALUES (%s, 1)"
            cursor.execute(sql, id_user)
        connection.commit()
    except Exception as e:
        raise HttpStatusCodeError(500, "Error giving basic rewards")
    finally:
        connection.close()
    return True
