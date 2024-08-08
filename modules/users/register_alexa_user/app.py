import json

from common.httpStatusCodeError import HttpStatusCodeError
from common.db_connection import get_db_connection


def lambda_handler(event, ___):
    try:
        body = json.loads(event['body'])

        validate_body(body)

        # Save user on DB
        save_user_db(body['id_user'], body['username'], 'M')

        # Give basic rewards
        give_basic_rewards(body['id_user'])

        # Get first title
        first_title = get_first_title()

        response = {
            'statusCode': 200,
            'body': first_title[0],
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
        }

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'body': json.dumps(str(e.message)),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(str(e)),
        }

    return response


def validate_body(body):
    """
    validate payload
    Args:
        body: payload
        - id_user: user of alexa (string)
        - username: username (string)
    """
    # Validate id_user
    if 'username' not in body:
        raise HttpStatusCodeError(400, "username is required")
    if body['username'] is None:
        raise HttpStatusCodeError(400, "username is required")
    if not isinstance(body['username'], str):
        raise HttpStatusCodeError(400, "username must be a string")

    if 'id_user' not in body:
        raise HttpStatusCodeError(400, "id_user is required")
    if body['id_user'] is None:
        raise HttpStatusCodeError(400, "id_user is required")

    return True


def save_user_db(id_user, username, gender):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO users (id_user, username, gender) VALUES (%s, %s, %s)"
            cursor.execute(sql, (id_user, username, gender))
        connection.commit()
    except Exception as e:
        raise HttpStatusCodeError(500, "Error inserting user")
    finally:
        connection.close()

    return True


def give_basic_rewards(id_user):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO user_rewards (id_user, id_reward) VALUES (%s, 1)"
            cursor.execute(sql, id_user)
        connection.commit()
    except Exception as e:
        raise HttpStatusCodeError(500, "Error giving basic rewards")
    finally:
        connection.close()
    return True


def get_first_title():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "SELECT wizard_title FROM rewards WHERE id_reward = 1"
            cursor.execute(sql)
            result = cursor.fetchone()
    except Exception as e:
        raise HttpStatusCodeError(500, "Error getting first title")
    finally:
        connection.close()
    return result
