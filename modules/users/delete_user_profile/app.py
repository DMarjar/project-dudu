import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from common.db_connection import get_db_connection
from common.httpStatusCodeError import HttpStatusCodeError

def lambda_handler(event, context):
    """ This function deletes a user profile and related data from the database and AWS Cognito

    event (dict): The event parameter is a dictionary that contains the following attributes:
        - body (str): The JSON string containing 'id' and other necessary attributes

    context (object): The context parameter is an object provided by AWS Lambda

    Returns:
        dict: A dictionary containing the status code and a message
    """

    try:
        body = json.loads(event['body'])

        # Validate payload
        validate_body(body)

        # Get secrets to delete the user on AWS Cognito
        secrets = get_secret()

        # Delete user profile from AWS Cognito
        delete_user_cognito(body['username'], secrets)

        # Delete user profile from DB
        delete_user_profile(body['id'])

        response = {
            'statusCode': 200,
            'body': json.dumps(f'User with id {body["id"]} deleted successfully')
        }

    except HttpStatusCodeError as e:
        print(e.message)
        response = {
            'statusCode': e.status_code,
            'body': json.dumps(e.message)
        }

    return response


# Validate payload
def validate_body(body):
    """ This function validates the payload"""

    # Validate id
    if 'id' not in body:
        raise HttpStatusCodeError(400, "Id is required")
    if not isinstance(body['id'], int) or body['id'] is None:
        raise HttpStatusCodeError(400, "Id must be a non-empty int")

    # Validate username
    if 'username' not in body:
        raise HttpStatusCodeError(400, "Username not in body, is required")
    if body['username'] is None:
        raise HttpStatusCodeError(400, "Username is none, is required")
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


def delete_user_cognito(username, secrets):
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = secrets['USER_POOL_ID']

    try:
        client.admin_delete_user(
            UserPoolId=user_pool_id,
            Username=username
        )
    except ClientError as e:
        raise HttpStatusCodeError(500, f"Error deleting user from Cognito -> {str(e)}")


# Delete user profile by id
def delete_user_profile(id):
    """ This function deletes a user profile and related data from the database by id

    id (int): The id of the user to be deleted

    Returns:
        bool: True if user profile deletion is successful
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (id,))
            if cursor.rowcount == 0:
                raise HttpStatusCodeError(404, "User not found")

        connection.commit()

    except Exception as e:
        raise e
    finally:
        connection.close()

    return True
