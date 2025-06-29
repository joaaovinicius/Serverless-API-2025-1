import json
import boto3
import base64
import uuid
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("tabela-teste")
s3 = boto3.resource("s3")
s3_client = boto3.client("s3")
bucket_name = "qualquer-um"  # Corrigido: underscore ao invés de hífen

def extrair_user_id_do_path(path):
    """
    Extrai userId do path para compatibilidade com API Gateway v2.0
    """
    parts = path.split('/')
    try:
        # Procura por UUID no path
        for part in parts:
            if len(part) == 36 and part.count('-') == 4:  # UUID format
                return part
    except:
        pass
    return None

def lambda_handler(event, context):
    """
    Função principal - identifica o método HTTP e roteia para a função apropriada
    """
    print(f"Event recebido: {json.dumps(event, indent=2)}")
    
    # 1. IDENTIFICAR O MÉTODO HTTP REQUISITADO
    # Compatibilidade com API Gateway v1.0 e v2.0
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('path') or event.get('rawPath', '')
    path_parameters = event.get('pathParameters') or {}
    
    print(f"Método HTTP: {http_method}")
    print(f"Path: {path}")
    
    try:
        # Roteamento baseado no método HTTP e path
        if http_method == 'POST' and '/upload' in path:
            user_id = extrair_user_id_do_path(path)
            return upload_arquivo(user_id, event)
            
        elif http_method == 'GET' and '/files' in path:
            user_id = extrair_user_id_do_path(path)
            return download_arquivos(user_id)
            
        elif http_method == 'POST' and '/users' in path and '/upload' not in path:
            return adicionar_usuario(event)
            
        elif http_method == 'GET' and '/users/' in path:
            user_id = path_parameters.get('userId') or extrair_user_id_do_path(path)
            return buscar_usuario(user_id)
            
        elif http_method == 'PUT' and '/users/' in path:
            user_id = path_parameters.get('userId') or extrair_user_id_do_path(path)
            return alterar_usuario(user_id, event)
            
        elif http_method == 'DELETE' and '/users/' in path:
            user_id = path_parameters.get('userId') or extrair_user_id_do_path(path)
            return remover_usuario(user_id)
            
        else:
            return resposta_erro(400, f"Rota não encontrada: {http_method} {path}")
            
    except Exception as e:
        print(f"Erro: {str(e)}")
        return resposta_erro(500, f"Erro interno: {str(e)}")

def adicionar_usuario(event):
    """
    2. ADICIONAR USUÁRIO À TABELA
    Recebe dados do body e insere no DynamoDB
    """
    try:
        # Parse do body da requisição
        body_raw = event.get('body', '{}')
        if isinstance(body_raw, str):
            body = json.loads(body_raw)
        else:
            body = body_raw
        
        print(f"Body parseado: {body}")
        
        # Validação básica
        if not body.get('nome'):
            return resposta_erro(400, "Campo 'nome' é obrigatório")
        
        # Gera ID único para o usuário
        user_id = str(uuid.uuid4())
        
        # Dados para inserir na tabela
        item = {
            "userId": user_id,
            "nome": body['nome'],
            "email": body.get('email', ''),
            "telefone": body.get('telefone', ''),
            "created_at": datetime.now().isoformat(),
            "arquivos": []  # Lista de arquivos vinculados
        }
        
        # Inserir no DynamoDB
        response = table.put_item(Item=item)
        
        return resposta_sucesso(201, {
            "message": "Usuário criado com sucesso",
            "userId": user_id,
            "usuario": item
        })
        
    except Exception as e:
        return resposta_erro(500, f"Erro ao criar usuário: {str(e)}")

def buscar_usuario(user_id):
    """
    Busca um usuário específico pelo ID
    """
    try:
        if not user_id:
            return resposta_erro(400, "userId é obrigatório")
        
        # Buscar no DynamoDB
        response = table.get_item(Key={"userId": user_id})
        
        if 'Item' not in response:
            return resposta_erro(404, "Usuário não encontrado")
        
        return resposta_sucesso(200, {
            "usuario": response['Item']
        })
        
    except Exception as e:
        return resposta_erro(500, f"Erro ao buscar usuário: {str(e)}")

def alterar_usuario(user_id, event):
    """
    3. ALTERAR DADOS DE UM USUÁRIO
    Atualiza campos específicos usando update_item
    """
    try:
        if not user_id:
            return resposta_erro(400, "userId é obrigatório")
        
        body_raw = event.get('body', '{}')
        if isinstance(body_raw, str):
            body = json.loads(body_raw)
        else:
            body = body_raw
        
        print(f"Body parseado: {body}")
        
        # Construir expressão de atualização dinamicamente
        update_expression = "SET updated_at = :updated_at"
        expression_values = {":updated_at": datetime.now().isoformat()}
        
        # Adicionar campos a serem atualizados
        if 'nome' in body:
            update_expression += ", nome = :nome"
            expression_values[":nome"] = body['nome']
        if 'email' in body:
            update_expression += ", email = :email"
            expression_values[":email"] = body['email']
        if 'telefone' in body:
            update_expression += ", telefone = :telefone"
            expression_values[":telefone"] = body['telefone']
        
        # Atualizar no DynamoDB
        response = table.update_item(
            Key={"userId": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        
        return resposta_sucesso(200, {
            "message": "Usuário atualizado com sucesso",
            "usuario": response['Attributes']
        })
        
    except Exception as e:
        return resposta_erro(500, f"Erro ao atualizar usuário: {str(e)}")

def remover_usuario(user_id):
    """
    4. REMOVER USUÁRIO DA TABELA
    Remove o registro do DynamoDB e todos os arquivos do S3
    """
    try:
        if not user_id:
            return resposta_erro(400, "userId é obrigatório")
        
        # Primeiro busca o usuário para pegar a lista de arquivos
        user_response = table.get_item(Key={"userId": user_id})
        
        if 'Item' not in user_response:
            return resposta_erro(404, "Usuário não encontrado")
        
        user_data = user_response['Item']
        
        # Remove arquivos do S3 se existirem
        if 'arquivos' in user_data and user_data['arquivos']:
            for arquivo in user_data['arquivos']:
                try:
                    s3_client.delete_object(Bucket=bucket_name, Key=arquivo['s3_key'])
                except Exception as e:
                    print(f"Erro ao deletar arquivo {arquivo['s3_key']}: {str(e)}")
        
        # Remove usuário do DynamoDB
        table.delete_item(Key={"userId": user_id})
        
        return resposta_sucesso(200, {
            "message": "Usuário e arquivos removidos com sucesso"
        })
        
    except Exception as e:
        return resposta_erro(500, f"Erro ao remover usuário: {str(e)}")

def upload_arquivo(user_id, event):
    """
    5. FAZER UPLOAD DE ARQUIVO E VINCULAR AO USUÁRIO
    Recebe arquivo em base64, salva no S3 e atualiza referência no DynamoDB
    """
    try:
        if not user_id:
            return resposta_erro(400, "userId é obrigatório")
        
        body = json.loads(event.get('body', '{}'))
        
        # Validações
        if not body.get('arquivo_base64'):
            return resposta_erro(400, "Campo 'arquivo_base64' é obrigatório")
        if not body.get('nome_arquivo'):
            return resposta_erro(400, "Campo 'nome_arquivo' é obrigatório")
        
        # Verifica se usuário existe
        user_response = table.get_item(Key={"userId": user_id})
        if 'Item' not in user_response:
            return resposta_erro(404, "Usuário não encontrado")
        
        # Decodifica arquivo base64
        arquivo_decoded = base64.b64decode(body['arquivo_base64'])
        
        # Gera chave única para o S3
        file_id = str(uuid.uuid4())
        s3_key = f"users/{user_id}/{file_id}_{body['nome_arquivo']}"
        
        # Upload para S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=arquivo_decoded,
            ContentType=body.get('content_type', 'application/octet-stream')
        )
        
        # Dados do arquivo para salvar no DynamoDB
        arquivo_info = {
            "file_id": file_id,
            "nome_original": body['nome_arquivo'],
            "s3_key": s3_key,
            "content_type": body.get('content_type', 'application/octet-stream'),
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Atualiza lista de arquivos do usuário
        table.update_item(
            Key={"userId": user_id},
            UpdateExpression="SET arquivos = list_append(if_not_exists(arquivos, :empty_list), :new_file)",
            ExpressionAttributeValues={
                ":empty_list": [],
                ":new_file": [arquivo_info]
            }
        )
        
        return resposta_sucesso(201, {
            "message": "Arquivo enviado com sucesso",
            "arquivo": arquivo_info
        })
        
    except Exception as e:
        return resposta_erro(500, f"Erro ao fazer upload: {str(e)}")

def download_arquivos(user_id):
    """
    6. FAZER DOWNLOAD DOS ARQUIVOS VINCULADOS AO USUÁRIO
    Retorna URLs pré-assinadas para download dos arquivos
    """
    try:
        if not user_id:
            return resposta_erro(400, "userId é obrigatório")
        
        # Busca dados do usuário
        user_response = table.get_item(Key={"userId": user_id})
        
        if 'Item' not in user_response:
            return resposta_erro(404, "Usuário não encontrado")
        
        user_data = user_response['Item']
        arquivos = user_data.get('arquivos', [])
        
        if not arquivos:
            return resposta_sucesso(200, {
                "message": "Usuário não possui arquivos",
                "arquivos": []
            })
        
        # Gera URLs pré-assinadas para download (válidas por 1 hora)
        arquivos_download = []
        for arquivo in arquivos:
            try:
                download_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': arquivo['s3_key']},
                    ExpiresIn=3600  # 1 hora
                )
                
                arquivos_download.append({
                    "file_id": arquivo['file_id'],
                    "nome_original": arquivo['nome_original'],
                    "download_url": download_url,
                    "uploaded_at": arquivo['uploaded_at']
                })
            except Exception as e:
                print(f"Erro ao gerar URL para {arquivo['s3_key']}: {str(e)}")
        
        return resposta_sucesso(200, {
            "arquivos": arquivos_download
        })
        
    except Exception as e:
        return resposta_erro(500, f"Erro ao buscar arquivos: {str(e)}")

def resposta_sucesso(status_code, data):
    """
    Função auxiliar para padronizar respostas de sucesso
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data, ensure_ascii=False)
    }

def resposta_erro(status_code, message):
    """
    Função auxiliar para padronizar respostas de erro
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': True,
            'message': message
        }, ensure_ascii=False)
    }

"""
EXEMPLOS DE USO DA API:

1. Adicionar usuário:
POST /users
Body: {"nome": "João", "email": "joao@email.com", "telefone": "123456789"}

2. Buscar usuário:
GET /users/{userId}

3. Alterar usuário:
PUT /users/{userId}
Body: {"nome": "João Silva", "email": "joao.silva@email.com"}

4. Remover usuário:
DELETE /users/{userId}

5. Upload arquivo:
POST /users/{userId}/upload
Body: {
    "arquivo_base64": "base64_encoded_file",
    "nome_arquivo": "documento.pdf",
    "content_type": "application/pdf"
}

6. Download arquivos:
GET /users/{userId}/files
"""