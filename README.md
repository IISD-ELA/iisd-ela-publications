# IISD-ELA Publications Search Engine

**Last Updated:** 2026-06-09

## Contents

* [Motivation](#motivation)
* [Usage](#usage)
* [Data Source](#data-source)
* [Architecture](#architecture)
* [AWS Deployment](#aws-deployment)
* [Testing](#testing)
* [Project Organization](#project-organization)
* [Contact and Support](#contact-and-support)

## Motivation

To help everyone discover IISD-ELA publications, this project provides a browser-based search interface backed by the IISD-ELA publications database in Google Sheets.

## Usage

- The search engine displays all quality-checked publications by default.
- Search results can be widened by selecting tags in "Search by data types", "Search by environmental issues", "Search by lakes", and "Search by authors". When multiple tags are selected, publications matching any selected tag are returned.
- Search results can be narrowed by "Filter by author type", "Year start", "Year end", and "General search". These filters only return publications that meet the selected or entered criteria.
- The "General search" field can match keywords that may not appear in citation text because backend records include additional publication metadata.
- Results are sorted alphabetically and formatted using APA 7th edition citation rules.
- Question mark icons beside each publication expose the associated metadata tags.

## Data Source

The publications data is pulled directly from a private backend Google Sheet using Google Sheets APIs. This database is updated on an ongoing basis to include IISD-ELA publications.

## Architecture

The deployed app is split into static browser assets and a small JSON API:

- **CloudFront** is the public entry point. It serves the browser app and routes `/api/*` plus `/health` to API Gateway.
- **S3** stores `static/index.html`, `static/app.js`, and `static/styles.css` in a private bucket. CloudFront reads the bucket through Origin Access Control, so the bucket is not public.
- **API Gateway HTTP API** exposes `GET /api/options`, `GET /api/search`, and `GET /health`, then invokes the Lambda function synchronously.
- **Lambda** runs the Python search backend from a zip artifact on the managed Python 3.14 runtime. It fetches publication data from Google Sheets, normalizes it, caches it briefly in the warm Lambda process, and returns JSON to the frontend.
- **SSM Parameter Store** holds runtime configuration. Google service account fields are read by Lambda at runtime, and the Google spreadsheet ID is read by OpenTofu and injected into Lambda as an environment variable during deploy.
- **Google Sheets API** is the source of record for publication and author data.

The request path is:

```text
Browser
  -> CloudFront
     -> S3 for /, /app.js, /styles.css
     -> API Gateway for /api/* and /health
        -> Lambda
           -> SSM Parameter Store for Google credentials
           -> Google Sheets API for publication data
```

The API is designed for same-origin browser use through CloudFront. The IISD site can embed the CloudFront page in an iframe; external JavaScript clients are not the primary deployment model.

## AWS Deployment

The AWS version is a static browser app backed by a zip-based AWS Lambda API:

- `static/` contains the HTML, CSS, and JavaScript frontend.
- `src/publications_app/` contains the Lambda handler and search logic.
- `requirements-lambda.txt` contains the Lambda dependency set.
- `infrastructure/publications/` contains the OpenTofu stack for Lambda, HTTP API Gateway, S3, CloudFront, IAM, and logs.
- `scripts/package-lambda.sh` builds `build/lambda.zip` in a Lambda-compatible Python 3.14 container.
- `scripts/start-local.sh` runs the app locally in a Lambda-compatible container.
- `scripts/deploy.sh` packages and deploys the app with OpenTofu.

The Lambda reads Google service account credentials from SSM Parameter Store under `/iisd-ela/config/publications/*`. The Google spreadsheet ID is also loaded from SSM at `/iisd-ela/config/publications/spreadsheet_id`; there is no spreadsheet ID fallback in the application code.

`scripts/deploy.sh` performs the deployment in this order:

1. Builds `build/lambda.zip` in the Lambda Python 3.14 container.
2. Runs `tofu init` and `tofu apply` in `infrastructure/publications`.
3. Uploads static files to the private S3 bucket through OpenTofu-managed `aws_s3_object` resources.
4. Updates the Lambda code and infrastructure.
5. Creates a CloudFront invalidation for `/*`.

Deploy with:

```bash
./scripts/deploy.sh -p iisd -r ca-central-1
```

Run locally with:

```bash
./scripts/start-local.sh -p iisd -r ca-central-1 -P 8080
```

## Testing

Run the Playwright suite against the deployed AWS app with:

```bash
npm run test:playwright
```

Run the Python unit tests with:

```bash
python -m pip install -r requirements-lambda.txt -r requirements-dev.txt
npm run test:python
```

The Playwright suite reads the deployed app URL from `tofu output -raw site_url` in `infrastructure/publications`. To compare the AWS app against another deployed baseline, provide the baseline URL:

```bash
BASELINE_PUBLICATIONS_URL="https://example.com/" \
npm run test:playwright
```

## Project Organization

```text
├── README.md
├── infrastructure
│   └── publications
│       ├── api-gateway.tf
│       ├── iam.tf
│       ├── lambda.tf
│       ├── static-site.tf
│       └── ...
├── package.json
├── playwright.config.js
├── requirements-lambda.txt
├── requirements-dev.txt
├── scripts
│   ├── deploy.sh
│   ├── package-lambda.sh
│   └── start-local.sh
├── src
│   └── publications_app
│       ├── config.py
│       ├── credentials.py
│       ├── google_sheets.py
│       ├── handler.py
│       ├── local_server.py
│       └── publications.py
├── static
│   ├── app.js
│   ├── index.html
│   └── styles.css
└── tests
    └── publications-search.spec.js
```

## Contact and Support

If you encounter any issues or bugs, or would like additional information about this search engine, contact eladata@iisd-ela.org.
