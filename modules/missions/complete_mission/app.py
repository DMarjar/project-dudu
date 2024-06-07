import json
from common.db_connection import get_db_connection


def lambda_handler(event, __):
    try:
        body = json.loads(event['body'])
        id_mission = body['id_mission']
        update_mission_status(id_mission, 'completed')
        response = {
            'statusCode': 200,
            'body': json.dumps({"message": f"Mission {id_mission} completed successfully"})
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({"message": f"An error occurred while completing the mission: {str(e)}"})
        }
    return response


def update_mission_status(id_mission, status):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE missions SET status = %s WHERE id_mission = %s"
            cursor.execute(sql, (status, id_mission))
            connection.commit()
    finally:
        connection.close()
