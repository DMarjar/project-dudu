import boto3
import openai
from botocore.exceptions import ClientError
from openai import OpenAI


# function to get openai client
def get_openai_client(original_description):
    secret = get_secret()

    # generate prompt
    prompt = ("Hola, ayudame a convertir unas frases en otras pero en forma epica, Te dare unos ejemplos de lo que "
              "quiero que hagas. Ejemplo 1 - Original: revizar los apuntes a mi compa - Convertida: Descifrar los "
              "antiguos jeroglíficos de un grimorio de otro mago ancestral; Ejemplo 2 - Original: jugar Fornite "
              "con amigos - Convertida: Reunirte con el gremio de magos para emprender una aventura a tierras "
              "peligrosas en busca de fama y gloria; Ejemplo 3 - Original: Buscar trabajo - Convertida: Emprender "
              "un viaje hacia nuevos horizontes en busca de aventura y recompenzas; Ejemplo 4 - Original : buscar "
              "un video de youtube para ver en el almuerzo - Convertida: Decidir quien sera el bufon del a corte "
              "que te atendera durante el festin real; Ejemplo 5 - Original: alimentar a mi perro - Convertida: "
              "alimentar a la vestia guardiana del palacio real. Como puedes ver es transformar pendientes en "
              "misiones epicas principalmente relacionadas con Magos, magia y fantasia. Solo quiero que me "
              "devuelvas la frase, no que me digas que entendiste u otra cosa, solo la frase convertida... Esta "
              "es la oracion que quiero que conviertas ahora: ") + original_description

    # create openai client with secret
    client = OpenAI(
        api_key=secret['openai_key']
    )

    # post request to openai
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="gpt-3.5-turbo"
    )

    return response.choices[0].message.content


# function to get secret from secrets manager
def get_secret():
    secret_name = "secret/openai/key"
    region_name = "us-east-2"

    # Create a Secrets Manager client
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
