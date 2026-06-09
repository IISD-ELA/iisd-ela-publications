resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 14
}

resource "aws_lambda_function" "publications" {
  function_name = local.lambda_function_name
  role          = aws_iam_role.lambda.arn

  filename         = abspath("${path.module}/${var.lambda_zip_path}")
  source_code_hash = filebase64sha256(abspath("${path.module}/${var.lambda_zip_path}"))
  handler          = "publications_app.handler.handler"
  runtime          = "python3.14"
  architectures    = ["x86_64"]

  timeout     = 29
  memory_size = 512

  environment {
    variables = {
      GOOGLE_SPREADSHEET_ID                     = data.aws_ssm_parameter.google_spreadsheet_id.value
      GOOGLE_SHEETS_CREDENTIAL_PARAMETER_PREFIX = var.google_credentials_parameter_prefix
      GOOGLE_SHEETS_MAX_ATTEMPTS                = "2"
      GOOGLE_SHEETS_TIMEOUT_SECONDS             = "9"
      PUBLICATIONS_CACHE_TTL_SECONDS            = tostring(var.publications_cache_ttl_seconds)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_ssm,
  ]
}
