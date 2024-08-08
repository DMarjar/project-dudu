import json
from common.db_connection import get_db_connection
from common.httpStatusCodeError import HttpStatusCodeError


def lambda_handler(event, ___):
    """ This function cancels a mission and updates its status in the database

    body (dict): The body parameter is a dictionary that contains the following attributes:
        - id_mission (int): The mission id to be cancelled
        - id_user (int): The user id performing the cancellation

    Returns:
        dict: A dictionary that contains the status code and a message
    """

    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
    }
    try:
        body = json.loads(event['body'])

        # Validate payload
        validate_body(body)

        # Validate existence of user
        validate_user(body['id_user'])

        # Cancel mission
        cancel_mission(body['id_mission'], body['id_user'])

        response = {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps("Mission cancelled successfully")
        }

    except HttpStatusCodeError as e:
        print(e.message)
        response = {
            'statusCode': e.status_code,
            'headers': headers,
            'body': json.dumps(e.message)
        }

    return response


# Validate payload
def validate_body(body):
    """ This function validates the payload"""

    # Validate id_mission
    if 'id_mission' not in body:
        raise HttpStatusCodeError(400, "id_mission is required")

    if body['id_mission'] is None:
        raise HttpStatusCodeError(400, "id_mission is required")

    if not isinstance(body['id_mission'], int):
        raise HttpStatusCodeError(400, "id_mission must be an integer")

    # Validate id_user
    if 'id_user' not in body:
        raise HttpStatusCodeError(400, "id_user is required")

    if body['id_user'] is None:
        raise HttpStatusCodeError(400, "id_user is required")

    if not isinstance(body['id_user'], int):
        raise HttpStatusCodeError(400, "id_user must be an integer")

    return True


# Validate existence of user
def validate_user(id_user):
    """ This function validates the existence of a user

    id_user (int): The user id

    Returns:
        bool: True if the user exists
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE id_user = %s"
            cursor.execute(sql, id_user)
            rows = cursor.fetchall()

            if len(rows) == 0:
                raise HttpStatusCodeError(404, "User not found")

    except Exception as e:
        raise e
    finally:
        connection.close()
    return True


# Cancel mission
def cancel_mission(id_mission, id_user):
    """ This function cancels a mission by updating its status in the database

    id_mission (int): The mission id to be cancelled
    id_user (int): The user id performing the cancellation

    Returns:
        bool: True if mission cancellation is successful
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "UPDATE missions SET status = %s WHERE id_mission = %s AND id_user = %s"
            cursor.execute(sql, ('cancelled', id_mission, id_user))
            if cursor.rowcount == 0:
                raise HttpStatusCodeError(404, "Mission not found or user unauthorized to cancel")

        connection.commit()

    except Exception as e:
        raise e
    finally:
        connection.close()

    return True
