import json

from .common.httpStatusCodeError import HttpStatusCodeError
from .common.db_connection import get_db_connection


def lambda_handler(event, ___):
    try:
        body = json.loads(event['body'])

        if 'id_user' not in body:
            raise HttpStatusCodeError(400, "id_user is required")

        id_user = body['id_user']

        if not check_user_exists(id_user):
            raise HttpStatusCodeError(200, False)

        response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': True
        }

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(e.message)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(str(e)),
        }

    return response


def check_user_exists(id_user):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = "SELECT * FROM users WHERE id_user = %s"
    cursor.execute(query, (id_user,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result is not None