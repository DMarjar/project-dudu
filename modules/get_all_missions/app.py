import json
from utils.db_connection import get_db_connection


def lambda_handler(_, __):
    try:
        missions = get_all_missions()
        print(missions)
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
        with connection.cursor() as cursor:
            sql = "SELECT * FROM missions"
            cursor.execute(sql)
            missions = cursor.fetchall()
    finally:
        connection.close()
    return missions
