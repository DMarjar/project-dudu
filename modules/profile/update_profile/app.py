import json
from common.db_connection import get_db_connection


def lambda_handler(event, __):
    try:
        body = json.loads(event['body'])
        if not body:
            response = {
                'statusCode': 400,
                'body': json.dumps({"message": "Bad request: Body is required"})
            }
            return response

        profile_id = body.get('id_profile')
        name = body.get('name')
        email = body.get('email')
        username = body.get('username')

        if profile_id is None:
            response = {
                'statusCode': 402,
                'body': json.dumps({"message": "Bad request: id is required"})
            }
            return response

        if isinstance(profile_id, int):
            update_profile(profile_id, name, email, username )
            response = {
                'statusCode': 200,
                'body': json.dumps({"message": f"Profile update successfully"})
            }
        else:
            response = {
                'statusCode': 404,
                'body': json.dumps({"message": "profile not updated"})
            }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({"message": f"An error occurred while completing the mission: {str(e)}"})
        }
    return response


def update_profile(profile_id, name, email, username):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Actualiza el estado de la misión
            sql_update = "UPDATE users SET name, email, username = %s WHERE profile_id = %s"
            cursor.execute(sql_update, (name, email, username, profile_id))
            connection.commit()
    finally:
        connection.close()