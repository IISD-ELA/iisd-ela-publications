resource "aws_apigatewayv2_api" "publications" {
  name          = "${local.name}-http-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "publications" {
  api_id                 = aws_apigatewayv2_api.publications.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.publications.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}

resource "aws_apigatewayv2_route" "api_options" {
  api_id    = aws_apigatewayv2_api.publications.id
  route_key = "GET /api/options"
  target    = "integrations/${aws_apigatewayv2_integration.publications.id}"
}

resource "aws_apigatewayv2_route" "api_search" {
  api_id    = aws_apigatewayv2_api.publications.id
  route_key = "GET /api/search"
  target    = "integrations/${aws_apigatewayv2_integration.publications.id}"
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.publications.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.publications.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.publications.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.publications.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.publications.execution_arn}/*/*"
}
