import json
from common.db_connection import get_db_connection


def lambda_handler(event, __):
    """ This function gets one mission

    Returns:
        dict: A dictionary that contains the mission's information
    """
    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, GET'
    }

    try:
        mission_id = event.get('pathParameters', {}).get('id_mission')

        if mission_id is None:
            response = {
                'statusCode': 400,
                'body': json.dumps("Mission id is required"),
                'headers': headers
            }
            return response

        mission = get_mission_by_id(mission_id)

        if mission is None:
            response = {
                'statusCode': 404,
                'body': json.dumps("Mission not found"),
                'headers': headers
            }
        else:
            response = {
                'statusCode': 200,
                'body': json.dumps(mission),
                'headers': headers
            }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred: {str(e)}"),
            'headers': headers
        }

    return response


def get_mission_by_id(mission_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM missions WHERE id_mission = %s"
            cursor.execute(sql, (mission_id,))
            row = cursor.fetchone()
            if row:
                column_names = [desc[0] for desc in cursor.description]
                mission = dict(zip(column_names, row))
                return mission
            else:
                return None
    finally:
        connection.close()
