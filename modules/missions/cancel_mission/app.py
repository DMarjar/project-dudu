import json
from modules.missions.cancel_mission.common.db_connection import get_db_connection


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
                    'body': json.dumps('La misión no existe o no pertenece al usuario')
                }
            update_sql = "UPDATE missions SET status = 'cancelled' WHERE id_user = %s AND id_mission = %s"
            cursor.execute(update_sql, (id_user, id_mission))
            connection.commit()

        return {
            'statusCode': 200,
            'body': json.dumps('La misión ha sido deshonrada por los Dioses')
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f"Un velo de oscuridad ha impedido la cancelación de la misión: {str(e)}")
        }
    finally:
        connection.close()
