import boto3
import json
from common.db_connection import get_db_connection


def lambda_handler(event, context):
    client = boto3.client('cognito-idp')

    username = event['username']
    client_id = '61eb6520-e0f1-7088-d053-ada0670b82ff'

    try:
        response = client.forgot_password(
            ClientId=client_id,
            Username=username
        )
        return {
            'statusCode': 200,
            'body': json.dumps('Password recovery initiated successfully.')
        }
    except client.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps('User not found.')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred: ' + str(e))
        }
