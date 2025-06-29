output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_stage.main_stage.invoke_url
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.main_lambda.function_name
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.main_table.name
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.main_bucket.id
}

output "aws_region" {
  description = "AWS region used"
  value       = var.aws_region
}

output "project_resources" {
  description = "Summary of created resources"
  value = {
    api_url     = aws_apigatewayv2_stage.main_stage.invoke_url
    lambda_name = aws_lambda_function.main_lambda.function_name
    table_name  = aws_dynamodb_table.main_table.name
    bucket_name = aws_s3_bucket.main_bucket.id
  }
}