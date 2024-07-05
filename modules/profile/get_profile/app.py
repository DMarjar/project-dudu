import json
import boto3
from common.db_connection import get_db_connection
from botocore.exceptions import ClientError, NoCredentialsError
from common.httpStatusCodeError import HttpStatusCodeError


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

        if profile_id is None:
            response = {
                'statusCode': 402,
                'body': json.dumps({"message": "Bad request: ID is required"})
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
            "cognito_data": cognito_data,
            "profile_data": profile
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
                SELECT u.id_user, u.level, u.current_xp, u.gender,
                       r.id_reward, r.image_wizard, r.image_sorceress, r.unlock_level
                FROM users u
                LEFT JOIN rewards r ON u.level >= r.unlock_level
                WHERE u.id_user = %s
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            if rows:
                profile_data = []
                for row in rows:
                    profile_data.append({
                        "id_user": row['id_user'],
                        "level": row['level'],
                        "current_xp": row['current_xp'],
                        "gender": row['gender'],
                        "rewards": {
                            "id_reward": row['id_reward'],
                            "image_wizard": row['image_wizard'],
                            "image_sorceress": row['image_sorceress'],
                            "unlock_level": row['unlock_level']
                        }
                    })
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
