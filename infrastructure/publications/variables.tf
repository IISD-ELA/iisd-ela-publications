variable "aws_region" {
  type    = string
  default = "ca-central-1"
}

variable "aws_profile" {
  type    = string
  default = "iisd"
}

variable "lambda_zip_path" {
  type    = string
  default = "../../build/lambda.zip"
}

variable "google_spreadsheet_id_parameter_name" {
  type    = string
  default = "/iisd-ela/config/publications/spreadsheet_id"
}

variable "google_credentials_parameter_prefix" {
  type    = string
  default = "/iisd-ela/config/publications"
}

variable "publications_cache_ttl_seconds" {
  type    = number
  default = 300
}
