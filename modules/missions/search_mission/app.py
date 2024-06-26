import json
from common.db_connection import get_db_connection
from pymysql.cursors import DictCursor
from common.httpStatusCodeError import HttpStatusCodeError


def lambda_handler(event, __):
    """ This function searches for a mission with name and/or filters

    body (dict): The body parameter is a dictionary that contains the following attributes:
        - id_user (int): The user id
        - search_query (str): The search query
        - order_by (str): The field to order the results
        - order (str): The order of the results
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

        # Search missions
        missions = search_mission(body)

        response = {
            'statusCode': 200,
            'body': json.dumps(missions)
        }

    except HttpStatusCodeError as e:
        response = {
            'statusCode': e.status_code,
            'body': json.dumps(e.message)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }

    return response


def validate_body(body):
    """ This function validates the body parameter

    Args:
        body (dict): The body parameter is a dictionary that contains the following attributes:
            - id_user (int): The user id
            - search_query (str): The search query
            - order_by (str): The field to order the results
            - order (str): The order of the results
            - status (str): The status of the mission
    """
    if 'id_user' not in body:
        raise HttpStatusCodeError(400, 'id_user is required')
    if 'search_query' not in body:
        raise HttpStatusCodeError(400, 'search_query is required')
    if 'order_by' not in body:
        raise HttpStatusCodeError(400, 'order_by is required')
    if 'order' not in body:
        raise HttpStatusCodeError(400, 'order is required')
    if 'status' not in body:
        raise HttpStatusCodeError(400, 'status is required')
    if body['order_by'] is None or body['order_by'] == '':
        raise HttpStatusCodeError(400, 'order_by cannot be null')
    if body['order'] is None or body['order'] == '':
        raise HttpStatusCodeError(400, 'order cannot be null')
    if body['status'] is None or body['status'] == '':
        raise HttpStatusCodeError(400, 'status cannot be null')
    if body['status'] not in ['pending', 'completed', 'cancelled', 'in_progress']:
        raise HttpStatusCodeError(400, 'Invalid status')

    return True


def validate_user(id_user):
    """ This function validates the existence of the user

    Args:
        id_user (int): The user id
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE id_user=%s"
            cursor.execute(sql, (id_user,))
            result = cursor.fetchall()
            if len(result) == 0:
                raise HttpStatusCodeError(404, 'User not found')
    finally:
        connection.close()
    return True


def search_mission(body):
    """ This function searches for a mission in the database with name and/or filters

    Args:
        body (dict): The body parameter is a dictionary that contains the following attributes:
            - id_user (int): The user id
            - search_query (str): The search query
            - order_by (str): The field to order the results
            - order (str): The order of the results
            - status (str): The status of the mission

    Returns:
        missions (list): A list of missions
    """
    connection = get_db_connection()
    try:
        with connection.cursor(DictCursor) as cursor:
            sql = ("SELECT * FROM missions "
                   "WHERE id_user=%s "
                   "AND (original_description LIKE %s "
                   "OR fantasy_description LIKE %s) "
                   "AND status=%s "
                   "ORDER BY %s %s")
            cursor.execute(sql, (body['id_user'], f"%{body['search_query']}%", f"%{body['search_query']}%",
                                 body['status'], body['order_by'], body['order']))
            missions = cursor.fetchall()
            return missions
    finally:
        connection.close()
