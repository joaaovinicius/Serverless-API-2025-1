# Use existing role from AWS Academy
data "aws_iam_role" "lambda_role" {
  name = "RoleForLambdaModLabRole"
}