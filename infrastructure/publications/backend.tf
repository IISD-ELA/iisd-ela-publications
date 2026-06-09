terraform {
  backend "s3" {
    bucket         = "terraform-state-iisd-ela"
    key            = "iisd-ela-publications/terraform.tfstate"
    region         = "ca-central-1"
    profile        = "iisd"
    dynamodb_table = "terraform-state-iisd-ela"
    encrypt        = true
  }
}
