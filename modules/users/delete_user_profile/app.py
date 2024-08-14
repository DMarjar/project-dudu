import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from common.db_connection import get_db_connection
from common.httpStatusCodeError import HttpStatusCodeError


def lambda_handler(event, context):
    """ This function deletes a user profile and related data from the database and AWS Cognito.

    event (dict): The event parameter is a dictionary that contains the following attributes:
        - body (str): The JSON string containing 'id_user'

    context (object): The context parameter is an object provided by AWS Lambda

    Returns:
        dict: A dictionary containing the status code and a message
    """

    try:
        body = json.loads(event['body'])
        validate_body_for_deletion(body)
        secrets = get_secret()

        # Eliminar el usuario en Cognito
        delete_cognito_user(body['sub'], secrets)

        # Eliminar el usuario en la base de datos
        delete_user_db(body['id_user'])

        response = {
            'statusCode': 200,
            'body': json.dumps("User deleted successfully")
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


# Validate payload
def validate_body_for_deletion(body):
    """
    Validate payload for deletion
    Args:
        body (dict): Payload
        - sub (str): User UUID from Cognito
        - id_user (str): User ID for database
    """
    # Validate sub
    if 'sub' not in body or not isinstance(body['sub'], str) or not body['sub']:
        raise HttpStatusCodeError(400, "sub is required and must be a non-empty string")

    # Validate id_user
    if 'id_user' not in body or not isinstance(body['id_user'], str) or not body['id_user']:
        raise HttpStatusCodeError(400, "id_user is required and must be a non-empty string")

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


def delete_cognito_user(sub, secrets):
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = secrets['USER_POOL_ID']

    try:
        response = client.admin_delete_user(
            UserPoolId=user_pool_id,
            Sub=sub
        )
    except client.exceptions.UserNotFoundException:
        raise HttpStatusCodeError(404, "User not found in Cognito")
    except client.exceptions.ClientError as e:
        raise HttpStatusCodeError(500, "Error deleting user in Cognito: " + str(e))


def delete_user_db(id_user):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE id_user = %s"
            cursor.execute(sql, (id_user,))
        connection.commit()
    except Exception as e:
        raise HttpStatusCodeError(500, "Database SQL Error: " + str(e))
    finally:
        connection.close()
