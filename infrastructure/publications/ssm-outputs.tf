resource "aws_ssm_parameter" "api_endpoint" {
  name        = "/iisd-ela/config/publications/api_endpoint"
  description = "Publications HTTP API endpoint used by shared application hosting"
  type        = "String"
  value       = aws_apigatewayv2_api.publications.api_endpoint
}
