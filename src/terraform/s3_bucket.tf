# S3 Bucket
resource "aws_s3_bucket" "main_bucket" {
  bucket = "${var.project_name}-${var.student_id}-bucket"
}

variable "student_id" {
  default = "lucas-bruzzone"
}