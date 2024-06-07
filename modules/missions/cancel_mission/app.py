import json
from common.db_connection import get_db_connection


def lambda_handler(event, __):
    connection = get_db_connection()
    id_user = event['id_user']
    id_mission = event['id_mission']
    try:
        with connection.cursor() as cursor:
            check_sql = "SELECT id_mission FROM missions WHERE id_user = %s AND id_mission = %s"
            cursor.execute(check_sql, (id_user, id_mission))
            mission = cursor.fetchone()
            if not mission:
                return {
                    'statusCode': 404,
                    'body': json.dumps('Mission not found')
                }
            update_sql = "UPDATE missions SET status = 'cancelled' WHERE id_user = %s AND id_mission = %s"
            cursor.execute(update_sql, (id_user, id_mission))
            connection.commit()

        return {
            'statusCode': 200,
            'body': json.dumps('Mission has been banished by the Gods')
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f"An error occurred while cancelling the mission: {str(e)}")
        }
    finally:
        connection.close()
