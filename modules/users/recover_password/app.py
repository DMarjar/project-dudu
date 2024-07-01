import boto3
import json
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError


def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def get_secret():
    secret_name = "users_pool/client_secret"
    region_name = "us-east-2"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']

    return json.loads(secret)


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
        secret_hash = get_secret_hash(email, client_id, client_secret)
        if not email:
            return {
                'statusCode': 404,
                'body': json.dumps('User email not found.')
            }
    except client.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps('User not found.')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred while checking user existence: ' + str(e))
        }

    # Iniciar recuperación de contraseña
    try:
        response = client.forgot_password(
            ClientId=client_id,
            Username=email,
            SecretHash=secret_hash
        )
        return {
            'statusCode': 200,
            'body': json.dumps(response['CodeDeliveryDetails'])
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred: ' + str(e))
        }
