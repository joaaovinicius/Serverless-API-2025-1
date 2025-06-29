# API Gateway HTTP
resource "aws_apigatewayv2_api" "main_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  description   = "Simple HTTP API Gateway"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_headers = ["content-type"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "main_stage" {
  api_id      = aws_apigatewayv2_api.main_api.id
  name        = "dev"
  auto_deploy = true
}

resource "aws_apigatewayv2_route" "health_route" {
  api_id    = aws_apigatewayv2_api.main_api.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.mock_integration.id}"
}

resource "aws_apigatewayv2_integration" "mock_integration" {
  api_id           = aws_apigatewayv2_api.main_api.id
  integration_type = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_apigatewayv2_integration_response" "mock_response" {
  api_id                   = aws_apigatewayv2_api.main_api.id
  integration_id           = aws_apigatewayv2_integration.mock_integration.id
  integration_response_key = "/200/"

  response_templates = {
    "application/json" = "{\"message\": \"API Gateway is healthy\"}"
  }
}

resource "aws_apigatewayv2_route_response" "health_response" {
  api_id             = aws_apigatewayv2_api.main_api.id
  route_id           = aws_apigatewayv2_route.health_route.id
  route_response_key = "$default"
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}