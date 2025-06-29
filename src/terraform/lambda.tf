# Lambda Function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../code"
  output_path = "lambda_function.zip"
}

resource "aws_lambda_function" "main_lambda" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-lambda"
  role             = data.aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.main_table.name
      S3_BUCKET      = aws_s3_bucket.main_bucket.id
    }
  }
}