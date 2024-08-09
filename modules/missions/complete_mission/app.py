import json
import random
from common.db_connection import get_db_connection


def lambda_handler(event, __):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS, GET, PUT, DELETE',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    try:
        body = json.loads(event['body'])
        if not body:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({"message": "Bad request: Body is required"})
            }

        id_mission = body.get('id_mission')
        id_user = body.get('id_user')

        if id_mission is None or id_user is None:
            return {
                'statusCode': 402,
                'headers': headers,
                'body': json.dumps({"message": "Bad request: id of mission and user is required"})
            }

        if isinstance(id_mission, int) and isinstance(id_user, int):
            # Inicia la transacción
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    #Verificar que el current_xp no sea mayor al xp_limit
                    cursor.execute("SELECT current_xp, xp_limit, level FROM users WHERE id_user = %s FOR UPDATE", (id_user,))
                    user = cursor.fetchone()
                    if not user:
                        raise Exception("User not found")

                    current_xp, xp_limit, level = user

                    if current_xp >= xp_limit:
                        raise Exception("User's XP is already at the limit")

                    # Crear un número random entre 1 y 25
                    random_xp = random.randint(1, 25)

                    # Completar la misión
                    cursor.execute("UPDATE missions SET status = 'completed' WHERE id_mission = %s", (id_mission,))

                    # Sumar el número random al current_xp
                    new_current_xp = current_xp + random_xp

                    # Verificar si al sumar el XP excede el límite
                    if new_current_xp >= xp_limit:
                        # Subir de nivel y resetear el XP
                        new_level = level + 1
                        new_current_xp = new_current_xp - xp_limit
                        new_limit_xp = xp_limit + 10
                        cursor.execute("UPDATE users SET level = %s, current_xp = %s, xp_limit = %s WHERE id_user = %s", (new_level, new_current_xp, new_limit_xp , id_user))
                    else:
                        # actualizar el XP
                        cursor.execute("UPDATE users SET current_xp = %s WHERE id_user = %s", (new_current_xp, id_user))

                    connection.commit()

                response = {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({"message": f"Mission {id_mission} completed successfully and XP updated"})
                }

            except Exception as e:
                connection.rollback()
                response = {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({"message": f"An error occurred: {str(e)}"})
                }

            finally:
                connection.close()

        else:
            response = {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({"message": "Invalid mission or user ID"})
            }

    except Exception as e:
        response = {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({"message": f"An error occurred: {str(e)}"})
        }

    return response
