import json
import boto3
from pymysql.cursors import DictCursor
from common.db_connection import get_db_connection
from botocore.exceptions import ClientError, NoCredentialsError
from common.httpStatusCodeError import HttpStatusCodeError


def lambda_handler(event, __):
    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    }
    try:
        if 'body' not in event:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({"message": "Bad request: Body is required"})
            }

        body = json.loads(event['body'])
        profile_id = body.get('id_user')

        if profile_id is None:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({"message": "Bad request: ID is required"})
            }

        if not isinstance(profile_id, str):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({"message": "Bad request: ID must be a string"})
            }

        if not profile_id.strip():
            return {
                'statusCode': 400,  # Adjusted to 400 for bad request
                'headers': headers,
                'body': json.dumps({"message": "Bad request: ID cannot be empty"})
            }

        user_found = validate_user(profile_id)

        if user_found['user_count'] == 0:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({"message": "User not found"})
            }

        profile = get_profile(profile_id)

        if not profile:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({"message": "No profile information found"})
            }

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'profile': profile
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({"message": f"An error occurred: {str(e)}"})
        }

    return response


def validate_user(user_id):
    connection = get_db_connection()
    try:
        with connection.cursor(DictCursor) as cursor:
            sql = """ SELECT COUNT(id_user) as user_count
                FROM users
                WHERE id_user = %s
            """
            cursor.execute(sql, (user_id,))
            user_data = cursor.fetchone()
            return user_data
    finally:
        connection.close()


def get_profile(user_id):
    connection = get_db_connection()
    try:
        with connection.cursor(DictCursor) as cursor:
            sql = """ SELECT u.id_user, 
       u.level, 
       u.current_xp, 
       u.gender, 
       u.username,
       u.xp_limit,
       r.id_reward, 
       r.unlock_level, 
       r.wizard_title,
       COUNT(CASE WHEN m.status = 'completed' THEN 1 END) AS completed_missions,
       COUNT(CASE WHEN m.status = 'failed' THEN 1 END) AS failed_missions,
       COUNT(CASE WHEN m.status = 'canceled' THEN 1 END) AS canceled_missions
FROM dududb.users u
LEFT JOIN dududb.rewards r ON u.level >= r.unlock_level
LEFT JOIN dududb.missions m ON u.id_user = m.id_user
WHERE u.id_user = %s
GROUP BY u.id_user, u.level, u.current_xp, u.gender, u.username, r.id_reward, r.unlock_level, r.wizard_title;
            """
            cursor.execute(sql, (user_id,))
            profile_data = cursor.fetchone()
            return profile_data
    finally:
        connection.close()


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
