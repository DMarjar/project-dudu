import json
import pymysql
import boto3
from botocore.exceptions import NoCredentialsError
from common.httpStatusCodeError import HttpStatusCodeError

DB_HOST = 'projectdudu-dbinstance-zxd8h1euhjhe.c7gis6w4srg8.us-east-2.rds.amazonaws.com'
DB_NAME = 'dududb'


def get_db_connection():
    secrets = get_secrets()
    host = DB_HOST
    user = secrets['username']
    password = secrets['password']
    db_name = DB_NAME

    try:
        return pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db_name
        )
    except pymysql.MySQLError:
        raise HttpStatusCodeError(500, "Error connecting to database")


def get_secrets():
    secret_name = "dudu/db/connection2"
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
    except NoCredentialsError:
        raise HttpStatusCodeError(500, "Error getting secret")

    secret = get_secret_value_response['SecretString']

    return json.loads(secret)