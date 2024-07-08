from unittest.mock import patch


def get_mock_secret_response():
    return {
        'SecretString': '{"username": "test_user", "password": "test_password"}'
    }


def mock_get_secrets():
    return {
        'username': 'test_user',
        'password': 'test_password'
    }


def patch_boto3_client():
    return patch('boto3.session.Session.client')


def patch_db_connection(module_name):
    return patch(f'{module_name}.get_db_connection')


def patch_get_secrets(module_name):
    return patch(f'{module_name}.get_secrets')


def configure_db_connection_test(mock_connect, mock_get_secrets_function, get_db_connection):
    mock_secrets = mock_get_secrets()
    mock_get_secrets_function.return_value = mock_secrets
    db_host = 'dududb.c7gis6w4srg8.us-east-2.rds.amazonaws.com'
    db_name = 'dududb'

    connection = get_db_connection()

    mock_get_secrets_function.assert_called_once()
    mock_connect.assert_called_once_with(
        host=db_host,
        user=mock_secrets['username'],
        password=mock_secrets['password'],
        db=db_name
    )
    return connection

