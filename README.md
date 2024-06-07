# Dungeons & Duties (DUDU)

## Descripción del Proyecto

**Dungeons & Duties** (nombre en clave: **DUDU**) es una aplicación de agenda de tareas con una arquitectura serverless. La particularidad de esta aplicación es que transforma la descripción de tus tareas en una narrativa fantasiosa y gamificada utilizando inteligencia artificial. 

### Características:
- **Transformación de tareas**: Convierte tareas cotidianas en misiones épicas.
- **Sistema de progresión**: Los usuarios suben de nivel, y su personaje cambia de apariencia y se vuelve más fuerte hasta el nivel máximo 50.
- **Arquitectura Serverless**: Utiliza AWS Lambda para garantizar escalabilidad y eficiencia.

## Requisitos Previos

- Cuenta de AWS
- Node.js y NPM instalados
- AWS CLI instalado y configurado
- Python 3.12
- Docker (para pruebas locales)

## Configuración del Proyecto

### 1. Crea un archivo app.py con un lambda_handler

   ```python
   def lambda_handler(event, context):
       return {
           'statusCode': 200,
           'body': json.dumps('Hello from Dungeons & Duties!')
       }
```

### 2. Agrega tu función dentro del `template.yaml`

```yaml
Resources:
  ExampleFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: path/to/your/code/
      Handler: app.lambda_handler
      Runtime: python3.12
      Role: !GetAtt LambdaExecutionRole.Arn
      Architectures:
        - x86_64
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref ExampleApi
            Path: /example_path
            Method: get

Outputs:
  ExampleFunctionUrl:
    Description: "URL for the Example function"
    Value: !Sub "https://${ExampleApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/example_path"
  ExampleFunctionArn:
    Description: "ARN for the Example function"
    Value: !GetAtt ExampleFunction.Arn
```


### 3. Agrega tus dependencias de función al workflow de GitHub Actions

```yaml
deploy:
  name: Deploy to AWS
  runs-on: ubuntu-latest
  needs: sonarcloud
  if: ${{ github.event_name == 'push' || github.event_name == 'pull_request' }}

  steps:
    - name: Install dependencies for example_function
      run: |
        cd path/to/your/code
        pip install -r requirements.txt
