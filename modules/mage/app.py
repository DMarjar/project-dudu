import json


def lambda_handler(____, ___):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps([
            {
                "id": 1,
                "name": "Toferatofe",
                "age": 2000,
                "rank": "Demon king",
                "magicType": {
                    "id": 1,
                    "name": "Fire",
                    "description": "Fire magic",
                    "element": "Fire",
                    "origin": "Fire"
                }

            },
            {
                "id": 2,
                "name": "Gandalf",
                "age": 2000,
                "rank": "Wizard",
                "magicType": {
                    "id": 2,
                    "name": "Wind",
                    "description": "Wind magic",
                    "element": "Wind",
                    "origin": "Wind"
                }
            },
            {
                "id": 3,
                "name": "Merlin",
                "age": 2000,
                "rank": "Wizard",
                "magicType": {
                    "id": 3,
                    "name": "Water",
                    "description": "Water magic",
                    "element": "Water",
                    "origin": "Water"
                }
            },
            {
                "id": 4,
                "name": "Saruman",
                "age": 2000,
                "rank": "Wizard",
                "magicType": {
                    "id": 4,
                    "name": "Earth",
                    "description": "Earth magic",
                    "element": "Earth",
                    "origin": "Earth"
                }
            },
            {
                "id": 5,
                "name": "Dumbledore",
                "age": 2000,
                "rank": "Wizard",
                "magicType": {
                    "id": 5,
                    "name": "Light",
                    "description": "Light magic",
                    "element": "Light",
                    "origin": "Light"
                }
            },
            {
                "id": 6,
                "name": "Voldemort",
                "age": 2000,
                "rank": "Dark wizard",
                "magicType": {
                    "id": 6,
                    "name": "Dark",
                    "description": "Dark magic",
                    "element": "Dark",
                    "origin": "Dark"
                }
            },
            {
                "id": 7,
                "name": "Goku",
                "age": 2000,
                "rank": "Saiyan",
                "magicType": {
                    "id": 7,
                    "name": "Ki",
                    "description": "Ki magic",
                    "element": "Ki",
                    "origin": "Ki"
                }
            },
            {
                "id": 8,
                "name": "Vegeta",
                "age": 2000,
                "rank": "Saiyan",
                "magicType": {
                    "id": 8,
                    "name": "Ki",
                    "description": "Ki magic",
                    "element": "Ki",
                    "origin": "Ki"
                }
            },
        ])
    }