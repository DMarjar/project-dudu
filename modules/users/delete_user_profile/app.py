import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from modules.users.delete_user_profile.common.db_connection import get_db_connection
from modules.users.delete_user_profile.common.httpStatusCodeError import HttpStatusCodeError


def lambda_handler(event, context):
    """ This function deletes a user profile and related data from the database and AWS Cognito.

    event (dict): The event parameter is a dictionary that contains the following attributes:
        - body (str): The JSON string containing 'sub'
        - body (str): The JSON string containing 'id_user'


    context (object): The context parameter is an object provided by AWS Lambda

    Returns:
        dict: A dictionary containing the status code and a message
    """

    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET, DELETE'
    }

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
            'headers': headers,
            'body': json.dumps("User deleted successfully")
        }

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'headers': headers,
            'body': json.dumps({"message": str(e)})
        }

    except ClientError as e:
        response = {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({"message": f"AWS Client Error: {str(e)}"})
        }

    except NoCredentialsError as e:
        response = {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({"message": f"Credentials Error: {str(e)}"})
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'headers': headers,
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

def get_username_from_sub(sub, user_pool_id):
    client = boto3.client('cognito-idp', region_name='us-east-2')

    # Obtén la lista de usuarios en el User Pool
    response = client.list_users(
        UserPoolId=user_pool_id,
        Filter=f'sub="{sub}"'
    )

    if response['Users']:
        return response['Users'][0]['Username']
    else:
        raise Exception("User not found")

def delete_cognito_user(sub, secrets):
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = secrets['USER_POOL_ID']

    #obtner el nombre de usuario basado en el sub
    username = get_username_from_sub(sub, user_pool_id)

    try:
        response = client.admin_delete_user(
            UserPoolId=user_pool_id,
            Username=username
        )
    except client.exceptions.UserNotFoundException:
        raise HttpStatusCodeError(404, "User not found in Cognito")
    except client.exceptions.ClientError as e:
        raise HttpStatusCodeError(500, "Error deleting user in Cognito: " + str(e))


def delete_user_db(id_user):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:

            delete_user_rewards_sql = "DELETE FROM user_rewards WHERE id_user = %s"
            cursor.execute(delete_user_rewards_sql, (id_user,))

            delete_user_sql = "DELETE FROM users WHERE id_user = %s"
            cursor.execute(delete_user_sql, (id_user,))

        connection.commit()
    except Exception as e:
        raise HttpStatusCodeError(500, "Database SQL Error: " + str(e))
    finally:
        connection.close()