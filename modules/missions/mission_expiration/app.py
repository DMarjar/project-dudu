import json
import datetime
from pymysql.cursors import DictCursor
from .common.db_connection import get_db_connection
from datetime import datetime



def lambda_handler(event, context):
    """ This function checks for expired missions and updates their status

    Returns:
        dict: A dictionary that contains the status code
              and a message indicating the expiration check is done
    """
    try:
        check_and_update_expired_missions()
        response = {
            'statusCode': 200,
            'body': json.dumps("Missions' expiration checking done")
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred while checking the missions: {str(e)}")
        }
    return response


def check_and_update_expired_missions():
    """ This function checks pending missions and updates the status to 'failed'
    if the current date is greater than the due date
    """
    connection = get_db_connection()
    try:
        with connection.cursor(DictCursor) as cursor:
            sql_select = "SELECT * FROM missions WHERE status = 'pending'"
            cursor.execute(sql_select)
            missions = cursor.fetchall()

            current_date = datetime.now().date()

            for mission in missions:
                due_date_str = mission['due_date']
                if due_date_str:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    if current_date > due_date:
                        sql_update = "UPDATE missions SET status = 'failed' WHERE id_mission = %s"
                        cursor.execute(sql_update, (mission['id_mission'],))
            connection.commit()
    finally:
        connection.close()
