import json
from modules.missions.insert_mission import app


def test_lambda_handler():
    mock_event = {
        'body': json.dumps({
            'original_description': 'bañar al perro porque ya esta bien sucio',
            'creation_date': '2024-06-07',
            'status': 'pending',
            'id_user': 1
        })
    }

    response = app.lambda_handler(mock_event, None)
    print(response)
