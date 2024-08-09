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
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT current_xp, xp_limit, level FROM users WHERE id_user = %s FOR UPDATE", (id_user,))
                    user = cursor.fetchone()
                    if not user:
                        raise Exception("User not found")

                    current_xp, xp_limit, level = user

                    if current_xp >= xp_limit:
                        raise Exception("User's XP is already at the limit")

                    random_xp = random.randint(10, 35)
                    cursor.execute("UPDATE missions SET status = 'completed' WHERE id_mission = %s", (id_mission,))
                    new_current_xp = current_xp + random_xp

                    if new_current_xp >= xp_limit:
                        new_level = level + 1
                        new_current_xp = new_current_xp - xp_limit
                        new_limit_xp = xp_limit + 10
                        cursor.execute("UPDATE users SET level = %s, current_xp = %s, xp_limit = %s WHERE id_user = %s",
                                       (new_level, new_current_xp, new_limit_xp, id_user))

                        # Retornar los datos del perfil actualizados
                        response = {
                            'statusCode': 200,
                            'headers': headers,
                            'body': json.dumps({
                                "message": f"Mission {id_mission} completed successfully and XP updated. Level Up!",
                                "user_profile": {
                                    "id_user": id_user,
                                    "level": new_level,
                                    "current_xp": new_current_xp,
                                    "xp_limit": new_limit_xp
                                }
                            })
                        }

                    else:
                        cursor.execute("UPDATE users SET current_xp = %s WHERE id_user = %s", (new_current_xp, id_user))
                        response = {
                            'statusCode': 200,
                            'headers': headers,
                            'body': json.dumps({"message": f"Mission {id_mission} completed successfully and XP updated"})
                        }

                    connection.commit()

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
