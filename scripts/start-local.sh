#!/bin/bash
set -eo pipefail

usage ()
{
  echo 'Runs the publications search app locally in a Lambda-compatible Python container.'
  echo ''
  echo 'Usage : start-local.sh -r <region> -p <profile> -P <port>'
  echo ''
  echo '-region      | -r <aws-region>  The target AWS region. Defaults to [ca-central-1]'
  echo '-profile     | -p <aws-profile> Name of the AWS profile. Defaults to [iisd]'
  echo '-port        | -P <port>        Local port. Defaults to [8080]'
  echo '-spreadsheet-parameter <name>   SSM parameter containing the Google spreadsheet ID.'
  exit 1
}

REGION='ca-central-1'
PROFILE='iisd'
PORT='8080'
SPREADSHEET_PARAMETER_NAME='/iisd-ela/config/publications/spreadsheet_id'

while [ "$1" != "" ]
do
    case $1 in
        -region|-r ) shift
                        REGION=$1
                        ;;
        -profile|-p ) shift
                        PROFILE=$1
                        ;;
        -port|-P ) shift
                        PORT=$1
                        ;;
        -spreadsheet-parameter ) shift
                        SPREADSHEET_PARAMETER_NAME=$1
                        ;;
        -help|-h ) usage
                        ;;
    esac
    shift
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="public.ecr.aws/lambda/python:3.14"

SPREADSHEET_ID="$(aws --profile "$PROFILE" --region "$REGION" ssm get-parameter \
  --name "$SPREADSHEET_PARAMETER_NAME" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)"

if [ -z "$SPREADSHEET_ID" ] || [ "$SPREADSHEET_ID" = "None" ]; then
  echo "Unable to load spreadsheet ID from SSM parameter: $SPREADSHEET_PARAMETER_NAME" >&2
  exit 1
fi

# Mount ~/.aws read-write so AWS SSO profiles can refresh token cache during local runs.
docker run --rm \
  --platform linux/amd64 \
  --entrypoint /bin/bash \
  -p "$PORT:8080" \
  -e AWS_PROFILE="$PROFILE" \
  -e AWS_REGION="$REGION" \
  -e AWS_DEFAULT_REGION="$REGION" \
  -e GOOGLE_SHEETS_CREDENTIAL_PARAMETER_PREFIX="/iisd-ela/config/publications" \
  -e GOOGLE_SPREADSHEET_ID="$SPREADSHEET_ID" \
  -v "$HOME/.aws:/root/.aws" \
  -v "$ROOT_DIR:/var/task" \
  "$IMAGE" \
  -lc 'set -eo pipefail
python -m pip install --no-cache-dir --target /tmp/publications-deps -r /var/task/requirements-lambda.txt
PYTHONPATH=/tmp/publications-deps:/var/task/src python -m publications_app.local_server --host 0.0.0.0 --port 8080'
