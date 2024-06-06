import json


def lambda_handler(event, ___):
    try:
        print("Inserting mission")
        body = json.loads(event['body'])

        response = {
            'statusCode': 200,
            'body': json.dumps("Mission inserted successfully")
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred while getting the missions: {str(e)}")
        }

    return response


def validate_body(body):
    if 'original_description' not in body:
        raise Exception("original_description is required")
    if 'creation_date' not in body:
        raise Exception("creation_date is required")
    if 'status' not in body:
        raise Exception("status is required")
    return True
