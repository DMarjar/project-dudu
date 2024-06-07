import json
from datetime import datetime
import boto3
from modules.missions.insert_mission.common.db_connection import get_db_connection


def lambda_handler(event, ___):
    try:
        print("Inserting mission")
        body = json.loads(event['body'])
        print(body)

        #validate payload
        validate_body(body)

        #validate existence of user
        validate_user(body['id_user'])

        response = {
            'statusCode': 200,
            'body': json.dumps("Mission inserted successfully")
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred while getting the missions: {str(e)}")
        }

    return response


#validate payload
def validate_body(body):
    #validate original_description###
    if 'original_description' not in body:
        raise Exception("original_description is required")

    #validate id_user###
    if 'id_user' not in body:
        raise Exception("id_user is required")

    #validate creation_date###
    if 'creation_date' not in body:
        raise Exception("creation_date is required")

    try:
        datetime.strptime(body['creation_date'], '%Y-%m-%d')
    except ValueError:
        raise Exception("Incorrect creation_date format, should be YYYY-MM-DD HH:MM:SS")

    #validate status###
    if 'status' not in body:
        raise Exception("status is required")

    if body['status'] not in ['pending', 'completed', 'cancelled', 'in_progress']:
        raise Exception("Status not valid")

    return True


#validate existence of user
def validate_user(id_user):
    connection = get_db_connection()
    try:

        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE id_user = %s"
            cursor.execute(sql, id_user)
            rows = cursor.fetchall()
            print(rows)
            if len(rows) == 0:
                raise Exception("User not found")
    finally:
        connection.close()
    return True
