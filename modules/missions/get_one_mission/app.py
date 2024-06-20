import json
from modules.missions.get_one_mission.db_connection import get_db_connection


def lambda_handler(event, __):
    try:
        mission_id = event.get('pathParameters', {}).get('id_mission')

        if mission_id is None:
            raise Exception("id_mission is required.")

        mission = get_mission_by_id(mission_id)
        response = {
            'statusCode': 200,
            'body': json.dumps(mission)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred: {str(e)}")
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