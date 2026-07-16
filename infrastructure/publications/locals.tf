data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_ssm_parameter" "google_spreadsheet_id" {
  name            = var.google_spreadsheet_id_parameter_name
  with_decryption = true
}

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host_header" {
  name = "Managed-AllViewerExceptHostHeader"
}

locals {
  account_id           = data.aws_caller_identity.current.account_id
  region               = data.aws_region.current.region
  name                 = "iisd-ela-publications-search"
  lambda_function_name = "${local.name}-api"
  static_bucket_name   = "${local.name}-${local.account_id}"
  static_origin_id     = "${local.name}-static"
  api_origin_id        = "${local.name}-api"
  static_dir           = abspath("${path.module}/../../static")
  static_files         = fileset(local.static_dir, "**/*")

  content_types = {
    ".css"  = "text/css"
    ".html" = "text/html"
    ".ico"  = "image/x-icon"
    ".js"   = "application/javascript"
    ".json" = "application/json"
    ".map"  = "application/json"
    ".png"  = "image/png"
    ".svg"  = "image/svg+xml"
    ".txt"  = "text/plain"
    ".webp" = "image/webp"
  }
}
