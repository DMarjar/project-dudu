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
        - page (int): The page number for pagination

    Returns:
        dict: A dictionary that contains the status code and a message, the mission list and the pagination information
    """
    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    }
    try:

        body = json.loads(event['body'])

        # Validate payload
        validate_body(body)

        # Validate existence of user
        validate_user(body['id_user'])

        # Search missions
        missions, total = search_mission(body)

        response = {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'missions': missions,
                'total': total
            })
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
    if 'page' not in body or not isinstance(body['page'], int) or body['page'] < 1:
        raise HttpStatusCodeError(400, 'invalid page')
    if body['order_by'] is None or body['order_by'] == '':
        raise HttpStatusCodeError(400, 'order_by cannot be null')
    if body['order'] is None or body['order'] == '':
        raise HttpStatusCodeError(400, 'order cannot be null')
    if body['status'] is None or body['status'] == '':
        raise HttpStatusCodeError(400, 'status cannot be null')
    if body['status'] not in ['pending', 'completed', 'cancelled', 'in_progress', 'failed']:
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
            limit = 1
            offset = (body['page'] - 1) * limit

            # Get the total number of missions
            sql = ("SELECT COUNT(*) as total FROM missions "
                   "WHERE id_user=%s "
                   "AND (original_description LIKE %s "
                   "OR fantasy_description LIKE %s) "
                   "AND status=%s")
            cursor.execute(sql, (body['id_user'], f"%{body['search_query']}%", f"%{body['search_query']}",
                                 body['status']))
            total = cursor.fetchone()['total']

            if total == 0:
                return []

            sql = ("SELECT id_mission, "
                   "original_description, "
                   "fantasy_description, "
                   "creation_date, "
                   "due_date, "
                   "status "
                   "FROM missions "
                   "WHERE id_user=%s "
                   "AND (original_description LIKE %s "
                   "OR fantasy_description LIKE %s) "
                   "AND status=%s "
                   "ORDER BY %s %s "
                   "LIMIT %s OFFSET %s")
            cursor.execute(sql, (body['id_user'], f"%{body['search_query']}%", f"%{body['search_query']}%",
                                 body['status'], body['order_by'], body['order'], limit, offset))
            missions = cursor.fetchall()
            return missions, total
    finally:
        connection.close()
