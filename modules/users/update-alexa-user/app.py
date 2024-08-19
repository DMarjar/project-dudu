import json

from common.httpStatusCodeError import HttpStatusCodeError
from common.db_connection import get_db_connection


def lambda_handler(event, ___):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS, GET, PUT, DELETE',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    """
        This function checks if a user exists only in the database
        it only works for the alexa skill
    """
    try:
        body = json.loads(event['body'])

        if 'id_user' not in body:
            raise HttpStatusCodeError(400, "id_user is required")
        if 'username' not in body:
            raise HttpStatusCodeError(400, "username is required")

        id_user = body['id_user']
        username = body['username']

        update_user(id_user, username)

        response = {
            'statusCode': 200,
            'headers': headers,
            'body': True
        }

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'headers': headers,
            'body': json.dumps(e.message)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(str(e)),
        }

    return response


def update_user(id_user, username):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE users SET username = %s WHERE id_user = %s", (username, id_user))
            connection.commit()
    finally:
        connection.close()

    return True
