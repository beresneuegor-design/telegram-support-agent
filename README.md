# Outreach Automation Toolkit

This repository contains two small Python automation tools:

- `enricher.py` for B2B lead enrichment
- `outreach.py` for personalized cold email generation and optional Gmail sending

## Included Tools

### 1. Lead Enrichment Pipeline

Reads a CSV of companies, finds likely websites, scrapes homepage data, and uses Gemini to infer business details.

Files:

- `enricher.py`
- `utils.py`
- `sample_input.csv`

Run:

```bash
python enricher.py --input sample_input.csv --output enriched_output.csv
```

Output columns:

- `company`
- `website`
- `email`
- `linkedin_url`
- `employee_count_estimate`
- `tech_stack`
- `summary`

### 2. Email Outreach Agent

Reads companies from CSV, scrapes their website homepage, uses Gemini to write a personalized cold email in English, and can send it via Gmail SMTP.

Files:

- `outreach.py`
- `email_generator.py`
- `gmail_sender.py`
- `sample_companies.csv`
- `email_template_context.txt`

Default behavior is safe dry-run mode. Emails are only sent when `--send` is passed.

Run in dry-run mode:

```bash
python outreach.py --input sample_companies.csv --output outreach_log.csv
```

Run with sending enabled:

```bash
python outreach.py --input sample_companies.csv --output outreach_log.csv --send
```

Log columns:

- `company`
- `email_sent_to`
- `subject`
- `status`
- `timestamp`

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Gemini API key

Windows:

```bash
set GEMINI_API_KEY=your_api_key
```

macOS or Linux:

```bash
export GEMINI_API_KEY=your_api_key
```

### 3. Set Gmail SMTP credentials for outreach sending

Windows:

```bash
set GMAIL_SENDER=your_email@gmail.com
set GMAIL_APP_PASSWORD=your_gmail_app_password
```

macOS or Linux:

```bash
export GMAIL_SENDER=your_email@gmail.com
export GMAIL_APP_PASSWORD=your_gmail_app_password
```

## Notes

- Output files act as checkpoints because processed companies are skipped on reruns.
- Missing data is written as empty strings where possible.
- Gemini failures do not crash the full run.
- Search and scraping depend on third-party site structure and may require maintenance over time.
