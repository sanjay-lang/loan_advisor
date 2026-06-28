# Render Deployment

## Recommended Setup

Use the Docker deployment path on Render. The included `Dockerfile` installs the native Linux libraries required by WeasyPrint before installing Python packages.

## Required Environment Variables

Set these in the Render service environment:

```text
RESEND_API_KEY=<your Resend API key>
RESEND_FROM_EMAIL=<optional verified sender, for example Loan Advisor <reports@yourdomain.com>>
GOOGLE_SHEETS_WEBHOOK_URL=<optional Google Sheets webhook>
```

## Render Settings

If using the included `render.yaml`, create the service from a Render Blueprint.

If creating the web service manually:

```text
Environment: Docker
Dockerfile Path: ./Dockerfile
Start Command: Use Dockerfile default
```

For a non-Docker Python service, use:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT app:app
```

The non-Docker path may fail PDF generation unless WeasyPrint native system libraries are available.

## Generated Files

Customer PDFs are generated under:

```text
reports/report_<timestamp>_<phone>.pdf
```

Generated reports and chart HTML files are ignored by git.
