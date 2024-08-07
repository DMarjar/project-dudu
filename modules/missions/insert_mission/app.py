import json
from datetime import datetime
from common.db_connection import get_db_connection
from common.openai_connection import get_openai_client
from common.httpStatusCodeError import HttpStatusCodeError


def lambda_handler(event, ___):
    """ This function generates a fantasy description for a mission and inserts it into the database

    body (dict): The body parameter is a dictionary that contains the following attributes:
        - original_description (str): The original description of the mission
        - id_user (int): The user id
        - creation_date (str): The creation date of the mission
        - status (str): The status of the mission

    Returns:
        dict: A dictionary that contains the status code and a message
    """

    try:
        body = json.loads(event['body'])

        # Validate payload
        validate_body(body)

        # Validate existence of user
        validate_user(body['id_user'])

        # Generate fantasy description
        fantasy_description = get_openai_client(body.get('original_description', ''))

        # Add fantasy description to body
        body['fantasy_description'] = fantasy_description

        # Insert mission
        insert_mission(body)

        response = {
            'statusCode': 200,
            'body': json.dumps(fantasy_description),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'body': json.dumps(e.message),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(str(e)),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }

    return response


# Validate payload
def validate_body(body):
    """ This function validates the payload"""

    # Validate original_description
    if 'original_description' not in body:
        raise HttpStatusCodeError(400, "original_description is required")

    if body['original_description'] is None:
        raise HttpStatusCodeError(400, "original_description is required")

    if not isinstance(body['original_description'], str):
        raise HttpStatusCodeError(400, "original_description must be a string")

    if len(body['original_description']) == 0:
        raise HttpStatusCodeError(400, "original_description cannot be empty")

    # Validate id_user
    if 'id_user' not in body:
        raise HttpStatusCodeError(400, "id_user is required")

    if body['id_user'] is None:
        raise HttpStatusCodeError(400, "id_user is required")

    # Validate creation_date
    if 'creation_date' not in body:
        raise HttpStatusCodeError(400, "creation_date is required")

    if body['creation_date'] is None:
        raise HttpStatusCodeError(400, "creation_date is required")

    try:
        datetime.strptime(body['creation_date'], '%Y-%m-%d')
    except ValueError:
        raise HttpStatusCodeError(400, "Incorrect creation_date format, should be YYYY-MM-DD")

    # Validate due_date
    if 'due_date' not in body:
        raise HttpStatusCodeError(400, "due_date is required")

    if body['due_date'] is None:
        raise HttpStatusCodeError(400, "due_date is required")

    try:
        datetime.strptime(body['due_date'], '%Y-%m-%d')
    except ValueError:
        raise HttpStatusCodeError(400, "Incorrect due_date format, should be YYYY-MM-DD")

    # Validate status
    if 'status' not in body:
        raise HttpStatusCodeError(400, "status is required")

    if body['status'] is None:
        raise HttpStatusCodeError(400, "status is required")

    if body['status'] not in ['pending', 'completed', 'cancelled', 'in_progress']:
        raise HttpStatusCodeError(400, "Invalid status")

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
    finally:
        connection.close()
    return True


# Insert mission
def insert_mission(body):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO missions (original_description, fantasy_description, creation_date, status, due_date, id_user) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (
                body['original_description'], body['fantasy_description'], body['creation_date'], body['status'], body['due_date'],
                body['id_user']))
        connection.commit()
    except Exception:
        raise HttpStatusCodeError(500, "Error inserting mission")
    finally:
        connection.close()
    return True
