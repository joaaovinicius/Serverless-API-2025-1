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

# API Gateway Integration with Lambda
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.main_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.main_lambda.invoke_arn
}

resource "aws_apigatewayv2_route" "lambda_route" {
  api_id    = aws_apigatewayv2_api.main_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "lambda_route_demo" {
  api_id    = aws_apigatewayv2_api.main_api.id
  route_key = "GET /demo"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "lambda_route_demo_aula" {
  api_id    = aws_apigatewayv2_api.main_api.id
  route_key = "POST /demo/aula"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main_api.execution_arn}/*/*"
}