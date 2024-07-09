import json
from common.db_connection import get_db_connection

def lambda_handler(event, __):
    try:
        body = json.loads(event['body'])
        if not body:
            response = {
                'statusCode': 400,
                'body': json.dumps({"message": "Bad request: Body is required"})
            }
            return response

        id_mission = body.get('id_mission')

        if id_mission is None:
            response = {
                'statusCode': 402,
                'body': json.dumps({"message": "Bad request: id of mission is required"})
            }
            return response

        if isinstance(id_mission, int):
            update_mission_status(id_mission, 'completed')
            response = {
                'statusCode': 200,
                'body': json.dumps({"message": f"Mission {id_mission} completed successfully"})
            }
        else:
            response = {
                'statusCode': 404,
                'body': json.dumps({"message": "Mission not found"})
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
            # Actualiza el estado de la misión
            sql_update = "UPDATE missions SET status = %s WHERE id_mission = %s"
            cursor.execute(sql_update, (status, id_mission))
            connection.commit()
    finally:
        connection.close()


