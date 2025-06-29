import json
import boto3
import os
import uuid
from datetime import datetime

# Configuração via variáveis de ambiente
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
S3_BUCKET = os.environ["S3_BUCKET"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)
s3 = boto3.client("s3")



def lambda_handler(event, context):
    """Função principal - roteia requisições HTTP"""

    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")

    try:
        if method == "POST" and "/users" in path:
            return create_user(event)
        elif method == "GET" and "/users/" in path:
            user_id = extract_user_id(path)
            return get_user(user_id)
        elif method == "PUT" and "/users/" in path:
            user_id = extract_user_id(path)
            return update_user(user_id, event)
        elif method == "DELETE" and "/users/" in path:
            user_id = extract_user_id(path)
            return delete_user(user_id)
        else:
            return response(404, {"error": "Route not found"})

    except Exception as e:
        return response(500, {"error": str(e)})


def extract_user_id(path):
    """Extrai userId do path"""
    parts = path.split("/")
    for part in parts:
        if len(part) == 36 and part.count("-") == 4:  # UUID format
            return part
    return None


def create_user(event):
    """Cria novo usuário"""
    body = json.loads(event.get("body", "{}"))

    if not body.get("nome"):
        return response(400, {"error": "Campo 'nome' é obrigatório"})

    user_id = str(uuid.uuid4())
    item = {
        "userId": user_id,
        "nome": body["nome"],
        "email": body.get("email", ""),
        "created_at": datetime.now().isoformat(),
    }

    table.put_item(Item=item)
    return response(201, {"message": "Usuário criado", "userId": user_id})


def get_user(user_id):
    """Busca usuário por ID"""
    if not user_id:
        return response(400, {"error": "userId é obrigatório"})

    result = table.get_item(Key={"userId": user_id})

    if "Item" not in result:
        return response(404, {"error": "Usuário não encontrado"})

    return response(200, {"user": result["Item"]})


def update_user(user_id, event):
    """Atualiza dados do usuário"""
    if not user_id:
        return response(400, {"error": "userId é obrigatório"})

    body = json.loads(event.get("body", "{}"))

    update_expr = "SET updated_at = :updated_at"
    expr_values = {":updated_at": datetime.now().isoformat()}

    if "nome" in body:
        update_expr += ", nome = :nome"
        expr_values[":nome"] = body["nome"]
    if "email" in body:
        update_expr += ", email = :email"
        expr_values[":email"] = body["email"]

    result = table.update_item(
        Key={"userId": user_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ReturnValues="ALL_NEW",
    )

    return response(
        200, {"message": "Usuário atualizado", "user": result["Attributes"]}
    )


def delete_user(user_id):
    """Remove usuário"""
    if not user_id:
        return response(400, {"error": "userId é obrigatório"})

    table.delete_item(Key={"userId": user_id})
    return response(200, {"message": "Usuário removido"})


def response(status_code, data):
    """Resposta padronizada"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, ensure_ascii=False),
    }
