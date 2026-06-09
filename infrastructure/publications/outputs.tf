output "site_url" {
  value = "https://${aws_cloudfront_distribution.publications.domain_name}"
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.publications.api_endpoint
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.publications.id
}

output "lambda_function_name" {
  value = aws_lambda_function.publications.function_name
}

output "static_bucket_name" {
  value = aws_s3_bucket.static.id
}
