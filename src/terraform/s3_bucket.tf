# # S3 Bucket
# resource "aws_s3_bucket" "main_bucket" {
#   bucket = "${var.project_name}-bucket-${random_string.suffix.result}"
# }

# resource "random_string" "suffix" {
#   length  = 8
#   special = false
#   upper   = false
# }