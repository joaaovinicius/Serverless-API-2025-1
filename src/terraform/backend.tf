terraform {
  backend "s3" {
    bucket = "terraform-state-aws-academy-2024"
    key    = "academy-lab/terraform.tfstate"
    region = "us-east-1"
  }
}