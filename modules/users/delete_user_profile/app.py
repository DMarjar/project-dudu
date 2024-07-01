import json
from modules.users.delete_user_profile.common.db_connection import get_db_connection
from modules.users.delete_user_profile.common.httpStatusCodeError import HttpStatusCodeError

def lambda_handler(event, context):
    """ This function deletes a user profile and related data from the database

    event (dict): The event parameter is a dictionary that contains the following attributes:
        - body (str): The JSON string containing 'username' and other necessary attributes

    context (object): The context parameter is an object provided by AWS Lambda

    Returns:
        dict: A dictionary containing the status code and a message
    """

    try:
        body = json.loads(event['body'])

        # Validate payload
        validate_body(body)

        # Delete user profile
        delete_user_profile(body['id'])

        response = {
            'statusCode': 200,
            'body': json.dumps(f'User with id {body["id"]} deleted successfully')
        }

    except HttpStatusCodeError as e:
        print(e.message)
        response = {
            'statusCode': e.status_code,
            'body': json.dumps(e.message)
        }

    return response


# Validate payload
def validate_body(body):
    """ This function validates the payload"""

    # Validate username
    if 'id' not in body:
        raise HttpStatusCodeError(400, "Id is required")

    if not isinstance(body['id'], int) or body['id'] is None:
        raise HttpStatusCodeError(400, "Id must be a non-empty int")

    return True


# Delete user profile by id_user
def delete_user_profile(id):
    """ This function deletes a user profile and related data from the database by id_user

    id_user (int): The id_user of the user to be deleted

    Returns:
        bool: True if user profile deletion is successful
    """

    connection = get_db_connection()  # Asegúrate de obtener la conexión a la base de datos

    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (id,))
            if cursor.rowcount == 0:
                raise HttpStatusCodeError(404, "User not found")

        connection.commit()

    except Exception as e:
        raise e
    finally:
        connection.close()

    return True
