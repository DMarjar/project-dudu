import json
from datetime import datetime
from common.db_connection import get_db_connection
from common.openai_connection import get_openai_client


def lambda_handler(event, ___):
    try:
        body = json.loads(event['body'])

        #validate payload
        validate_body(body)

        #validate existence of user
        validate_user(body['id_user'])

        #Generate fantasy description
        fantasy_description = get_openai_client(body.get('original_description', ''))

        #add fantasy description to body
        body['fantasy_description'] = fantasy_description

        #insert mission
        insert_mission(body)

        response = {
            'statusCode': 200,
            'body': json.dumps("Mission inserted successfully")
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred while getting the missions: {str(e)} - {event}")
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
            if len(rows) == 0:
                raise Exception("User not found")
    except Exception as e:
        raise e
    finally:
        connection.close()
    return True


#insert mission
def insert_mission(body):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO missions (original_description, fantasy_description, creation_date, status, id_user) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (
            body['original_description'], body['fantasy_description'], body['creation_date'], body['status'],
            body['id_user']))
        connection.commit()
    except Exception as e:
        raise e
    finally:
        connection.close()
    return True
