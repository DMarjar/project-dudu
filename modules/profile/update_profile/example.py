import json
import boto3
from modules.profile.get_profile.common.db_connection import get_db_connection
from botocore.exceptions import ClientError, NoCredentialsError
from .common.httpStatusCodeError import HttpStatusCodeError


def lambda_handler(event, __):
    try:
        profile_id = event.get('pathParameters', {}).get('id_user')

        if profile_id is None:
            response = {
                'statusCode': 402,
                'body': json.dumps({"message": "Bad request: ID is required"})
            }
            return response

        if not isinstance(profile_id, str):
            response = {
                'statusCode': 402,
                'body': json.dumps({"message": "Bad request: ID must be a string"})
            }
            return response

        if not profile_id.strip():
            response = {
                'statusCode': 402,
                'body': json.dumps({"message": "Bad request: ID cannot be empty"})
            }
            return response

        # Obtener datos de Cognito
        secrets = get_secret()

        cognito_data = get_cognito_data(profile_id, secrets)
        if not cognito_data:
            return {
                'statusCode': 404,
                'body': json.dumps({"message": "User not found in Cognito"})
            }

        # Obtener datos de la base de datos
        profile = get_profile(profile_id)
        if not profile:
            return {
                'statusCode': 404,
                'body': json.dumps({"message": "User not found in the database"})
            }

        combined_data = {
            "cognito_data": {
                "username": cognito_data.get('username', ''),
                "email": cognito_data.get('email', '')
            },
            "profile_data": {
                "gender": profile.get('gender', ''),
            }
        }

        response = {
            'statusCode': 200,
            'body': json.dumps(combined_data)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({"message": f"An error occurred: {str(e)}"})
        }

    return response


def get_cognito_data(user_id, secrets):
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = secrets['USER_POOL_ID']

    try:
        response = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=user_id
        )
        attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
        cognito_data = {
            "username": attributes.get('preferred_username', ''),
            "email": attributes.get('email', '')
        }
        return cognito_data
    except client.exceptions.UserNotFoundException:
        return None


def get_profile(user_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT u.gender
                FROM users u
                WHERE u.id_user = %s
            """
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            if row:
                profile_data = {
                    "gender": row['gender']
                }
                return profile_data
            else:
                return None
    finally:
        connection.close()


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
