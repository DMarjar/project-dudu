import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from modules.users.delete_user_profile.common.db_connection import get_db_connection
from modules.users.delete_user_profile.common.httpStatusCodeError import HttpStatusCodeError


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

        # Delete user profile from AWS Cognito
        delete_user_cognito(body['id_user'], secrets)

        # Delete user profile from DB
        delete_user_profile(body['id_user'])

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


def delete_user_cognito(id_user, secrets):
    if not id_user or not isinstance(id_user, str):
        raise HttpStatusCodeError(400, "Id_user must be a non-empty string")

    client = boto3.client('cognito-idp')
    try:
        client.admin_delete_user(
            UserPoolId=secrets['USER_POOL_ID'],
            Username=id_user
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            raise HttpStatusCodeError(404, "User not found in Cognito")
        else:
            raise HttpStatusCodeError(500, "Error deleting user from Cognito")
    except NoCredentialsError:
        raise HttpStatusCodeError(500, "No credentials found")


# Delete user profile by UUID (sub)
def delete_user_profile(id_user):
    """ This function deletes a user profile and related data from the database by id_user

    id_user (str): The UUID (sub) of the user to be deleted

    Returns:
        bool: True if user profile deletion is successful
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE uuid = %s"
            cursor.execute(sql, (id_user,))
            if cursor.rowcount == 0:
                raise HttpStatusCodeError(404, "User not found in the database")

        connection.commit()

    except Exception as e:
        raise e
    finally:
        connection.close()

    return True
