import boto3
import json
from botocore.exceptions import ClientError
from common.common_functions import get_secret, get_secret_hash


def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    }

    client = boto3.client('cognito-idp')
    secrets = get_secret()
    body = json.loads(event['body'])
    username = body['username']
    confirmation_code = body['confirmation_code']
    new_password = body['new_password']
    confirm_new_password = body['confirm_new_password']

    client_id = secrets['ID_CLIENT']
    client_secret = secrets['SECRET_CLIENT']

    if new_password != confirm_new_password:
        return {
            'statusCode': 400,
            'body': json.dumps('New password and confirmation password do not match.'),
            'headers': headers
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

        return {
            'statusCode': 200,
            'body': json.dumps('Password has been reset successfully.'),
            'headers': headers
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'CodeMismatchException':
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid confirmation code.'),
                'headers': headers
            }
        elif error_code == 'ExpiredCodeException':
            return {
                'statusCode': 400,
                'body': json.dumps('Confirmation code has expired.'),
                'headers': headers
            }
        elif error_code == 'InvalidPasswordException':
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid password.'),
                'headers': headers
            }
        elif error_code == 'UserNotFoundException':
            return {
                'statusCode': 404,
                'body': json.dumps('User not found.'),
                'headers': headers
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps('An error occurred while resetting the password: ' + str(e)),
                'headers': headers
            }
