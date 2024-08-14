import json
import re
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from common.httpStatusCodeError import HttpStatusCodeError
from common.db_connection import get_db_connection


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        validate_body(body)
        secrets = get_secret()

        # Actualizar el usuario en Cognito
        update_cognito_user(body['sub'], body, secrets)

        # Actualizar el usuario en la base de datos
        update_user_db(body['id_user'], body['gender'])

        response = {
            'statusCode': 200,
            'body': json.dumps("User updated successfully")
        }

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'body': json.dumps({"message": str(e)})
        }

    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({"message": f"AWS Client Error: {str(e)}"})
        }

    except NoCredentialsError as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({"message": f"Credentials Error: {str(e)}"})
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({"message": f"An unexpected error occurred: {str(e)}"})
        }

    return response


def validate_body(body):
    """
    Validate payload
    Args:
        body (dict): Payload
        - sub (str): User UUID from Cognito
        - id_user (str): User ID for database
        - email (str): User email
        - username (str): User username
        - gender (str): M or F
    """
    # Validate sub
    if 'sub' not in body:
        raise HttpStatusCodeError(400, "sub is required")
    if body['sub'] is None:
        raise HttpStatusCodeError(400, "sub is required")
    if not isinstance(body['sub'], str):
        raise HttpStatusCodeError(400, "sub must be a string")

    # Validate id_user
    if 'id_user' not in body:
        raise HttpStatusCodeError(400, "id_user is required")
    if body['id_user'] is None:
        raise HttpStatusCodeError(400, "id_user is required")
    if not isinstance(body['id_user'], str):
        raise HttpStatusCodeError(400, "id_user must be a string")

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
    if body['gender'] not in ['M', 'F']:
        raise HttpStatusCodeError(400, "invalid gender value, must be M or F")

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
        raise HttpStatusCodeError(500, "Error getting secret from AWS Secrets Manager: " + str(e))
    except NoCredentialsError as e:
        raise HttpStatusCodeError(500, "AWS Credentials Error: " + str(e))

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


def update_cognito_user(sub, body, secrets):
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = secrets['USER_POOL_ID']

    try:
        response = client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=sub,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': body['email']
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                }
            ]
        )
    except client.exceptions.UserNotFoundException:
        raise HttpStatusCodeError(404, "User not found in Cognito")
    except ClientError as e:
        raise HttpStatusCodeError(500, "Error updating user in Cognito: " + str(e))


def update_user_db(id_user, gender):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "UPDATE users SET gender = %s WHERE id_user = %s"
            cursor.execute(sql, (gender, id_user))
        connection.commit()
    except Exception as e:
        raise HttpStatusCodeError(500, "Database SQL Error: " + str(e))
    finally:
        connection.close()
