# UPDATER: Shelter Data Management

This repository contains two main Python scripts for managing and auditing shelter (sikringsrum) data in Denmark, integrating with Supabase and public APIs (BBR and DAR).

## Table of Contents
- [Overview](#overview)
- [Scripts](#scripts)
  - [new_shelters.py](#new_shelterspy)
  - [shelter_audit.py](#shelter_auditpy)
- [Setup & Configuration](#setup--configuration)
- [Usage](#usage)
- [API & Database](#api--database)
- [Notes](#notes)

---

## Overview

These scripts automate the discovery, updating, and auditing of shelter data:
- **new_shelters.py**: Discovers and adds new shelters from the BBR API to a Supabase database.
- **shelter_audit.py**: Audits existing shelters in the database, updating or soft-deleting records that are outdated or invalid.

Both scripts use the BBR and DAR APIs for authoritative building and address data, and store results in a Supabase PostgreSQL database.

---

## Scripts

### new_shelters.py

**Purpose:**
- Scans all Danish municipalities (kommuner) for new shelters (buildings with shelter capacity) using the BBR API.
- Adds new shelters to the `sheltersv2` table in Supabase, including address and capacity info from the DAR API.
- Tracks progress per municipality and supports resuming interrupted runs.

**Key Features:**
- Fetches and resumes from the last processed page for each municipality.
- Avoids duplicates by checking existing shelter IDs.
- Can process a specific municipality by passing its code as a command-line argument.
- Marks municipalities as complete when finished.

**Usage:**
```bash
python new_shelters.py [kommunekode]
```
- If `kommunekode` is provided, only that municipality is processed.
- Otherwise, the next municipality in the queue is processed.

---

### shelter_audit.py

**Purpose:**
- Audits all shelters in the database that have not been checked in the last 30 days (or never checked).
- For each shelter:
  - Fetches the latest data from BBR and DAR APIs.
  - Updates shelter info if anything has changed.
  - Soft-deletes shelters that are no longer valid (e.g., no longer have shelter capacity, wrong status, or missing in BBR).

**Key Features:**
- Uses robust retry logic for API requests.
- Logs all actions and errors.
- Soft-deletes by marking records with a timestamp and reason, not physical deletion.

**Usage:**
```bash
python shelter_audit.py
```
- No arguments needed. Processes all outdated shelters.

---

## Setup & Configuration

1. **Python Requirements:**
   - Python 3.7+
   - Install dependencies:
     ```bash
     pip install requests urllib3 python-dotenv
     ```

2. **Environment Variables:**
   - Create a `.env` file in the project root with the following variables:
     ```env
     SUPABASE_URL=your_supabase_url
     SUPABASE_KEY=your_supabase_key
     BBR_API_URL=your_bbr_api_url
     DAR_API_URL=your_dar_api_url
     DATAFORDELER_USERNAME=your_datafordeler_username
     DATAFORDELER_PASSWORD=your_datafordeler_password
     ```
   - The scripts will automatically load these variables using `python-dotenv`.

3. **Supabase Database:**
   - The scripts expect a Supabase table `sheltersv2` with fields for shelter info, and a `kommunekoder` table for tracking municipality progress.
   - See the scripts for expected field names.

---

## API & Database

- **BBR API**: Used to fetch building (shelter) data.
- **DAR API**: Used to fetch address data for shelters.
- **Supabase**: Used as the main database for storing and updating shelter records.

---

## Notes

- **Sensitive Data**: All API keys and credentials are now loaded from environment variables in a `.env` file. Do not commit your `.env` file to version control.
- **Error Handling**: Both scripts include error handling and logging, but you should monitor logs for failed updates or API issues.
- **Extending**: You can adapt the scripts for other types of building audits or data sources by modifying the API queries and database schema.

---

For more details, see comments in each script.
