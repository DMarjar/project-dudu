import boto3
import json
from common.common_functions import get_secret, get_secret_hash


def lambda_handler(event, context):
    client = boto3.client('cognito-idp')
    secret = get_secret()

    body = json.loads(event['body'])
    username = body['username']
    confirmation_code = body['confirmation_code']
    new_password = body['new_password']
    confirm_new_password = body['confirm_new_password']
    client_id = '4iid9n3o306aorf0imcs0dcplo'
    client_secret = secret['SECRET_CLIENT']

    if new_password != confirm_new_password:
        return {
            'statusCode': 400,
            'body': json.dumps('New password and confirmation password do not match.'),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }

    try:
        secret_hash = get_secret_hash(username, client_id, client_secret)

        response = client.confirm_forgot_password(
            ClientId=client_id,
            Username=username,
            ConfirmationCode=confirmation_code,
            Password=new_password,
            SecretHash=secret_hash
        )

        response['headers'] = {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        }

        return {
            'statusCode': 200,
            'body': json.dumps('Password has been reset successfully.'),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
    except client.exceptions.CodeMismatchException:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid confirmation code.'),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
    except client.exceptions.ExpiredCodeException:
        return {
            'statusCode': 400,
            'body': json.dumps('Confirmation code has expired.'),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
    except client.exceptions.InvalidPasswordException as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f'Invalid password: {str(e)}'),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
    except client.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps('User not found.'),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred while resetting the password: ' + str(e)),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
