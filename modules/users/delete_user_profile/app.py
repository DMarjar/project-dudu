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

        # Validate payload
        validate_body(body)

        # Get secrets to delete the user in AWS Cognito
        secrets = get_secret()

        # Get the username from AWS Cognito using id_user
        username = get_username_cognito(body['id_user'], secrets)

        # Delete user profile from DB
        delete_user_profile(body['id_user'])

        # Delete user profile from AWS Cognito
        delete_user_cognito(username, secrets)

        response = {
            'statusCode': 200,
            'body': json.dumps(f'User with id {body["id_user"]} deleted successfully')
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
    """ This function validates the payload """

    # Validate id_user
    if 'id_user' not in body:
        raise HttpStatusCodeError(400, "Id_user is required")
    if not isinstance(body['id_user'], str) or body['id_user'].strip() == "":
        raise HttpStatusCodeError(400, "Id_user must be a non-empty string")

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


def get_username_cognito(id_user, secrets):
    client = boto3.client('cognito-idp')
    try:
        response = client.list_users(
            UserPoolId=secrets['USER_POOL_ID'],
            Filter=f'sub = "{id_user}"'
        )
        if not response['Users']:
            raise HttpStatusCodeError(404, "User not found in Cognito")

        username = response['Users'][0]['Username']
        return username
    except ClientError as e:
        raise HttpStatusCodeError(500, "Error retrieving username from Cognito")


def delete_user_cognito(username, secrets):
    if not username or not isinstance(username, str):
        raise HttpStatusCodeError(400, "Username must be a non-empty string")

    client = boto3.client('cognito-idp')
    try:
        client.admin_delete_user(
            UserPoolId=secrets['USER_POOL_ID'],
            Username=username
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            raise HttpStatusCodeError(404, "User not found in Cognito")
        else:
            raise HttpStatusCodeError(500, "Error deleting user from Cognito")
    except NoCredentialsError:
        raise HttpStatusCodeError(500, "No credentials found")


def delete_user_profile(id_user):
    """ This function deletes a user profile and related data from the database by id_user

    id_user (str): The UUID (sub) of the user to be deleted

    Returns:
        bool: True if user profile deletion is successful
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE id_user = %s"
            cursor.execute(sql, (id_user,))
            if cursor.rowcount == 0:
                raise HttpStatusCodeError(404, "User not found in the database")

        connection.commit()

    except Exception as e:
        raise e
    finally:
        connection.close()

    return True
