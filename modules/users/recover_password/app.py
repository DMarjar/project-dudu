import boto3
import json
from common.common_functions import get_secret, get_secret_hash


def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    }

    client = boto3.client('cognito-idp', region_name='us-east-2')
    secrets = get_secret()

    body = json.loads(event['body'])
    username = body['username']

    client_id = "739rrbctbufv3tbr652n35kjfn"
    client_secret = secrets['SECRET_CLIENT']

    try:
        user = client.admin_get_user(
            UserPoolId=secrets['USER_POOL_ID'],
            Username=username
        )

        email = next((attr['Value'] for attr in user['UserAttributes'] if attr['Name'] == 'email'), None)
        email_verified = next((attr['Value'] for attr in user['UserAttributes'] if attr['Name'] == 'email_verified'),
                              'false')
        user_status = user['UserStatus']

        if not email:
            return {
                'statusCode': 404,
                'body': json.dumps(f'User email not found. {client_id}'),
                'headers': headers
            }

        if email_verified != 'true':
            return {
                'statusCode': 400,
                'body': json.dumps('User email not verified.'),
                'headers': headers
            }

        if user_status != 'CONFIRMED':
            return {
                'statusCode': 400,
                'body': json.dumps("User account hasn't been confirmed."),
                'headers': headers
            }

    except client.exceptions.UserNotFoundException as e:
        return {
            'statusCode': 404,
            'body': json.dumps(f'User not found: {str(e)} {client_id}'),
            'headers': headers
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred while checking user existence: ' + str(e)),
            'headers': headers
        }

    try:
        secret_hash = get_secret_hash(email, client_id, client_secret)

        response = client.forgot_password(
            ClientId=client_id,
            Username=email,
            SecretHash=secret_hash
        )

        response['headers'] = headers

        return {
            'statusCode': 200,
            'body': json.dumps(response['CodeDeliveryDetails']),
            'headers': headers
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred: ' + str(e) + client_id),
            'headers': headers
        }
