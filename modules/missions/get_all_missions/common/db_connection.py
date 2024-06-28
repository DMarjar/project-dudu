import json
import pymysql
import boto3

DB_HOST = 'dududb.c7gis6w4srg8.us-east-2.rds.amazonaws.com'
DB_NAME = 'dududb'


def get_db_connection():
    secrets = get_secrets()
    host = DB_HOST
    user = secrets['username']
    password = secrets['password']
    db_name = DB_NAME

    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        db=db_name
    )


def get_secrets():
    secret_name = "dudu/db/connection"
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
    except Exception as e:
        raise e

    secret = get_secret_value_response['SecretString']

    return json.loads(secret)
