import json
<<<<<<< HEAD
=======
from pymysql.cursors import DictCursor
>>>>>>> 7fb4870c92375fd1b937a958ff9201d2d1fff65d
from modules.missions.get_all_missions.common.db_connection import get_db_connection


def lambda_handler(__, ___):
    """ This function gets all pending missions

    Returns:
        dict: A dictionary that contains the status code
              and a list of missions or a message if no missions are found
    """

    try:
        missions = get_all_missions()

        if not missions:
            response = {
                'statusCode': 204,
                'body': json.dumps("No missions found")
            }
            return response

        response = {
            'statusCode': 200,
            'body': json.dumps(missions)
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred while getting the missions: {str(e)}")
        }
    return response


def get_all_missions():
    """ This function gets the pending missions from the database

    Returns:
        list: A list of pending missions
    """
    connection = get_db_connection()
    try:
        with connection.cursor(DictCursor) as cursor:
            sql = "SELECT * FROM missions WHERE status = 'pending'"
            cursor.execute(sql)
            missions = cursor.fetchall()
            return missions
    finally:
        connection.close()
