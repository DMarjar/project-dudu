import json
from common.db_connection import get_db_connection
from pymysql.cursors import DictCursor


def lambda_handler(__, ___):
    try:
        missions = get_all_missions()
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
    connection = get_db_connection()
    try:
        with connection.cursor(DictCursor) as cursor:
            sql = "SELECT * FROM missions where status = 'in_progress'"
            cursor.execute(sql)
            missions = cursor.fetchall()
    finally:
        connection.close()
    return missions
