import boto3
import json
from common.common_functions import get_secret, get_secret_hash


def lambda_handler(event, context):
    client = boto3.client('cognito-idp')
    secret = get_secret()

    body = json.loads(event['body'])
    username = body['username']
    client_id = '4iid9n3o306aorf0imcs0dcplo'
    client_secret = secret['SECRET_CLIENT']

    try:
        user = client.admin_get_user(
            UserPoolId='us-east-2_bjlyJabGh',
            Username=username
        )

        email = next((attr['Value'] for attr in user['UserAttributes'] if attr['Name'] == 'email'), None)
        email_verified = next((attr['Value'] for attr in user['UserAttributes'] if attr['Name'] == 'email_verified'),
                              'false')
        user_status = user['UserStatus']

        if not email:
            return {
                'statusCode': 404,
                'body': json.dumps('User email not found.'),
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                }
            }

        if email_verified != 'true':
            return {
                'statusCode': 400,
                'body': json.dumps('User email not verified.'),
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                }
            }

        if user_status != 'CONFIRMED':
            return {
                'statusCode': 400,
                'body': json.dumps("User account hasn't been confirmed."),
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
            'body': json.dumps('An error occurred while checking user existence: ' + str(e)),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }

    try:
        secret_hash = get_secret_hash(email, client_id, client_secret)

        response = client.forgot_password(
            ClientId=client_id,
            Username=email,
            SecretHash=secret_hash
        )
        return {
            'statusCode': 200,
            'body': json.dumps(response['CodeDeliveryDetails']),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred: ' + str(e)),
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
