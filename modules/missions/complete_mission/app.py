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
        # Verificar si el cuerpo está ausente
        if 'body' not in event or event['body'] is None:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({"message": "Bad request: Body is required"})
            }

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
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({"message": "Bad request: id of mission and user is required"})
            }

        if isinstance(id_mission, int) and isinstance(id_user, str):
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT current_xp, xp_limit, level FROM users WHERE id_user = %s FOR UPDATE",
                                   (id_user))
                    user = cursor.fetchone()
                    if not user:
                        raise Exception("User not found")

                    current_xp, xp_limit, level = user

                    if current_xp >= xp_limit:
                        raise Exception("User's XP is already at the limit")

                    random_xp = random.randint(10, 35)
                    cursor.execute("UPDATE missions SET status = 'completed' WHERE id_mission = %s", (id_mission))
                    new_current_xp = current_xp + random_xp

                    if new_current_xp >= xp_limit:
                        new_level = level + 1
                        if new_level > 50:
                            new_level = 50
                            new_current_xp = xp_limit  # Ensure XP doesn't go above the limit
                        else:
                            new_current_xp = new_current_xp - xp_limit
                            new_limit_xp = xp_limit + 10
                            cursor.execute(
                                "UPDATE users SET level = %s, current_xp = %s, xp_limit = %s WHERE id_user = %s",
                                (new_level, new_current_xp, new_limit_xp, id_user))

                            max_reward_id = 11
                            if new_level % 5 == 0:
                                cursor.execute("SELECT id_reward FROM user_rewards WHERE id_user = %s", (id_user,))
                                reward_increment = cursor.fetchone()[0]
                                reward_increment += 1
                        
                            if reward_increment > 0:
                                new_reward_id = min(reward_increment, max_reward_id)

                                cursor.execute("UPDATE user_rewards SET id_reward = %s where id_user = %s",
                                               (new_reward_id, id_user))

                                cursor.execute("SELECT wizard_title FROM rewards WHERE id_reward = %s",
                                               (new_reward_id,))
                                reward = cursor.fetchone()
                                reward_title = reward[0] if reward else "Unknown Reward"
                            else:
                                reward_title = None

                        response = {
                            'statusCode': 200,
                            'headers': headers,
                            'body': json.dumps({
                                "message": f"Mission {id_mission} completed successfully and XP updated. Level Up!",
                                "id_user": id_user,
                                "level": new_level,
                                "current_xp": new_current_xp,
                                "xp_limit": xp_limit,
                                "level_up": True,
                                "xp": random_xp,
                                # "reward_title": reward_title,
                                # "reward_increment": reward_increment,
                                # "new_reward_id": new_reward_id
                            })
                        }

                    else:
                        cursor.execute("UPDATE users SET current_xp = %s WHERE id_user = %s", (new_current_xp, id_user))
                        response = {
                            'statusCode': 200,
                            'headers': headers,
                            'body': json.dumps({
                                "message": f"Mission {id_mission} completed successfully and XP updated",
                                "id_user": id_user,
                                "level": level,
                                "current_xp": new_current_xp,
                                "xp_limit": xp_limit,
                                "level_up": False,
                                "xp": random_xp,
                                "no entro": True
                            })
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
                'statusCode': 400,
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
