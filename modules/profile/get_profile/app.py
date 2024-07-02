import json
from common.db_connection import get_db_connection


def lambda_handler(event, __):
    try:
        profile_id = event.get('pathParameters', {}).get('id_profile')

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

        profile = get_profile(profile_id)
        response = {
            'statusCode': 200,
            'body': json.dumps(profile)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred: {str(e)}")
        }

    return response


def get_profile(profile_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE id_profile = %s" #luego lo cambio
            cursor.execute(sql, (profile_id,))
            row = cursor.fetchone()
            if row:
                column_names = [desc[0] for desc in cursor.description]
                profile = dict(zip(column_names, row))
                return profile
            else:
                return None
    finally:
        connection.close()