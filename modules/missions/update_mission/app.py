import json
from modules.missions.update_mission.common.db_connection import get_db_connection

def lambda_handler(event, context):
    try:
        print("event ", event)
        body = json.loads(event['body'])  # Deserializar el cuerpo del evento
        id_task = body['id_task']
        update_mission_status(id_task, 'completed')
        response = {
            'statusCode': 200,
            'body': json.dumps({"message": f"Mission {id_task} completed successfully"})
        }
        print("hola response", response)
    except Exception as e:
        print("este es el error", e)
        response = {
            'statusCode': 500,
            'body': json.dumps({"message": f"An error occurred while completing the mission: {str(e)}"})
        }
    return response

def update_mission_status(id_task, status):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE task SET status = %s WHERE id_task = %s"
            cursor.execute(sql, (status, id_task))
            connection.commit()
    finally:
        connection.close()
