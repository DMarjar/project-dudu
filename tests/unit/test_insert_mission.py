import json
from modules.missions.insert_mission import app


def test_lambda_handler():
    mock_event = {
        'body': json.dumps({
            'original_description': 'bañar al perro porque ya esta bien sucio',
            'creation_date': 'creation_date',
            'status': 'status'
        })
    }

    response = app.lambda_handler(mock_event, None)
    print(response)
