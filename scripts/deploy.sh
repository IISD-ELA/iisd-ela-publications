#!/bin/bash
set -eo pipefail

usage ()
{
  echo 'Deploys the IISD-ELA publications search app.'
  echo ''
  echo 'Usage: deploy.sh [-r <region>] [-p <profile>] [-m <deploy|plan|apply|assets>]'
  echo ''
  echo '-region | --region | -r <aws-region>   Defaults to AWS_REGION or ca-central-1'
  echo '-profile | --profile | -p <aws-profile> Defaults to AWS_PROFILE or iisd'
  echo '--mode       | -m <mode>        Defaults to deploy'
  echo ''
  echo 'With no mode, package and deploy in one step using OpenTofu auto-approval.'
  echo 'plan: package and save a plan without uploading shared assets.'
  echo 'apply: apply the saved plan and publish its built shared assets.'
  echo 'assets: rebuild and publish only shared assets, leaving the original hosting and backend unchanged.'
  echo 'Positional plan, apply and assets modes remain supported.'
  echo 'Requires AWS CLI, jq, Docker and (except for assets mode) OpenTofu.'
  exit 0
}

fail() {
  echo "Error: $*" >&2
  exit 2
}

REGION="${AWS_REGION:-ca-central-1}"
PROFILE="${AWS_PROFILE:-iisd}"
MODE=
while [[ $# -gt 0 ]]; do
  case "$1" in
    -region|--region|-r)
      [[ $# -ge 2 && -n "$2" && "$2" != -* ]] || fail "$1 requires a region"
      REGION="$2"; shift 2 ;;
    -profile|--profile|-p)
      [[ $# -ge 2 && -n "$2" && "$2" != -* ]] || fail "$1 requires a profile"
      PROFILE="$2"; shift 2 ;;
    -help|--help|-h) usage; exit 0 ;;
    -m|--mode)
      [[ $# -ge 2 && -n "$2" && "$2" != -* ]] || fail "$1 requires a mode"
      [[ -z "$MODE" ]] || fail 'Specify only one mode: deploy, plan, apply or assets'
      MODE="$2"; shift 2 ;;
    plan|apply|assets)
      [[ -z "$MODE" ]] || fail 'Specify only one mode: deploy, plan, apply or assets'
      MODE="$1"; shift ;;
    *) fail "Unknown argument: $1" ;;
  esac
done
MODE="${MODE:-deploy}"
case "$MODE" in
  deploy|plan|apply|assets) ;;
  *) fail "Unknown mode: $MODE" ;;
esac

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR="$ROOT_DIR/build/site"
PLAN="$ROOT_DIR/build/dashboard.tfplan"
APP_PREFIX=publications
AWS=(aws --profile "$PROFILE" --region "$REGION")

load_shared_hosting() {
  local parameters config ssm_prefix=/iisd-ela/config/hosting
  parameters="$("${AWS[@]}" ssm get-parameters \
    --names "$ssm_prefix/bucket" "$ssm_prefix/distribution_id" \
      "$ssm_prefix/site_url" "$ssm_prefix/app_prefixes" --output json)"
  config="$(jq -e --arg root "$ssm_prefix/" '
    if ((.InvalidParameters // []) | length) != 0 or (.Parameters | length) != 4 then
      error("Missing shared hosting parameters")
    else
      .Parameters | map({key: (.Name | ltrimstr($root)), value: .Value}) | from_entries
    end
  ' <<< "$parameters")" || fail 'Missing shared hosting parameters in SSM'
  # Fail closed before any uploads or deletes if the destination is unexpected.
  jq -e --arg prefix "$APP_PREFIX" '
    .bucket == "iisd-ela-apps-static-105984564492" and
    (.distribution_id | type == "string" and test("^E[A-Z0-9]+$")) and
    .site_url == "https://apps.iisd-ela.org" and
    (.app_prefixes | type == "string" and (split(",") | index($prefix) != null))
  ' <<< "$config" > /dev/null || fail 'Invalid shared hosting configuration in SSM'
  SHARED_BUCKET="$(jq -r .bucket <<< "$config")"
  SHARED_DISTRIBUTION_ID="$(jq -r .distribution_id <<< "$config")"
  SHARED_SITE_URL="$(jq -r .site_url <<< "$config")/$APP_PREFIX/"
}

invalidate() {
  local distribution="$1" invalidation
  shift
  invalidation="$("${AWS[@]}" cloudfront create-invalidation \
    --distribution-id "$distribution" --paths "$@" --query Invalidation.Id --output text)"
  echo "Waiting for CloudFront invalidation: $invalidation"
  "${AWS[@]}" cloudfront wait invalidation-completed \
    --distribution-id "$distribution" --id "$invalidation"
}

publish_shared_assets() {
  [[ -s "$SITE_DIR/index.html" ]] || fail 'Missing built index.html; refusing to synchronize assets'
  local destination="s3://$SHARED_BUCKET/$APP_PREFIX/"
  # Upload dependencies first, application JS/CSS next, and HTML last.
  # Both deletions are restricted to this app's prefix; excluded files are protected.
  "${AWS[@]}" s3 sync "$SITE_DIR/" "$destination" --delete \
    --exclude '*.html' --exclude 'app.js' --exclude 'styles.css' \
    --cache-control 'public, max-age=60'
  # Copy even unchanged app files so existing objects receive the cache metadata.
  "${AWS[@]}" s3 cp "$SITE_DIR/" "$destination" --recursive \
    --exclude '*' --include 'app.js' --include 'styles.css' --cache-control 'no-cache'
  "${AWS[@]}" s3 sync "$SITE_DIR/" "$destination" --delete \
    --exclude '*' --include '*.html' --cache-control 'no-cache'
  invalidate "$SHARED_DISTRIBUTION_ID" "/$APP_PREFIX" "/$APP_PREFIX/*"
  echo "Shared site URL: $SHARED_SITE_URL"
}

pushd "$ROOT_DIR" > /dev/null

if [[ "$MODE" == apply ]]; then
  [[ -f "$PLAN" ]] || fail 'No saved plan. Run deploy.sh --mode plan first.'
fi
if [[ "$MODE" != plan ]]; then
  load_shared_hosting
fi
if [[ "$MODE" != apply ]]; then
  scripts/package-lambda.sh
fi
[[ -s "$SITE_DIR/index.html" ]] || fail 'Missing built index.html; refusing to deploy'

if [[ "$MODE" == assets ]]; then
  publish_shared_assets
  exit 0
fi

pushd "infrastructure/publications" > /dev/null
tofu init -reconfigure \
  -backend-config="region=$REGION" \
  -backend-config="profile=$PROFILE"

case "$MODE" in
  plan)
    tofu plan -input=false -var="aws_region=$REGION" -var="aws_profile=$PROFILE" -out="$PLAN"
    printf 'Review with: tofu -chdir=%q show %q\n' "$ROOT_DIR/infrastructure/publications" "$PLAN"
    printf 'Apply with: %q --mode apply -p %q -r %q\n' "$ROOT_DIR/scripts/deploy.sh" "$PROFILE" "$REGION"
    exit 0
    ;;
  apply)
    tofu apply -input=false "$PLAN"
    ;;
  deploy)
    tofu apply -auto-approve -input=false \
      -var="aws_region=$REGION" \
      -var="aws_profile=$PROFILE"
    ;;
esac

DISTRIBUTION_ID="$(tofu output -raw cloudfront_distribution_id)"
SITE_URL="$(tofu output -raw site_url)"
API_ENDPOINT="$(tofu output -raw api_endpoint)"

popd > /dev/null

invalidate "$DISTRIBUTION_ID" '/*'
publish_shared_assets
echo "Site URL: $SITE_URL"
echo "API endpoint: $API_ENDPOINT"

popd > /dev/null
