# Setup Guide

This guide explains how to set up the GraphQL-based Shelter Sync system.

## 1. Prerequisites

### Accounts & Access
1.  **Supabase:** Create a project and get your `URL` and `service_role` key.
2.  **Datafordeler:** Register at [datafordeler.dk](https://datafordeler.dk).
    *   You need an **API Key** (Web-service nøgle) for GraphQL access.

## 2. Local Setup

### Installation
```bash
git clone https://github.com/svanecode/Shelter-updater.git
cd Shelter-updater
pip install -r requirements.txt
```

### Configuration
Create a `.env` file from the example:
```bash
cp .env.example .env
```

Fill in the following variables:
*   `SUPABASE_URL`: Your Supabase project URL.
*   `SUPABASE_KEY`: Your Supabase `service_role` key.
*   `DATAFORDELER_API_KEY`: Your Datafordeler GraphQL API Key.

Optional tuning variables:
*   `ADDRESS_REFRESH_DAYS`: Days before refreshing address data (default 90).
*   `PAGE_SIZE`: GraphQL page size (default 500).
*   `GRAPHQL_PAGE_SLEEP`: Delay between pages in seconds (default 0.2).
*   `DAR_SLEEP_TIME`: Delay between address lookups in seconds (default 0.1).
*   `MAX_GRAPHQL_RETRIES`: Retries per GraphQL page (default 8).
*   `GRAPHQL_RETRY_BASE_SLEEP`: Backoff base seconds (default 5).
*   `SAFE_THRESHOLD`: Minimum seen records before deletions (default 500).
*   `MIN_DELETE_COVERAGE`: Minimum coverage ratio for deletions (default 0.8).

## 3. Database Setup

1.  Open the **SQL Editor** in your Supabase dashboard.
2.  Copy and run the contents of `sql/init_db.sql`.
    *   This creates the `sheltersv2` table with the required unique constraints and indexes.

## 4. Running the Sync

### Manual Run
```bash
python sync_shelters_graphql.py
```
The script will:
1.  Load existing shelters from Supabase.
2.  Query BBR GraphQL for all active shelters.
3.  Update changed records, add new ones (fetching addresses from DAR), and soft-delete missing ones.

### Automated Run (GitHub Actions)
The repository is pre-configured with a GitHub Action (`.github/workflows/shelter-sync-graphql.yml`) that runs daily at 04:00 UTC.

To enable it:
1.  Go to your GitHub Repository **Settings** -> **Secrets and variables** -> **Actions**.
2.  Add the required environment variables from your `.env` as **Secrets**.
3.  Ensure Actions are enabled in the **Actions** tab.

The workflow also uploads a `sync_summary.json` artifact and writes a summary to the GitHub Actions job summary.

## 5. Troubleshooting

*   **400 Bad Request (GraphQL):** Usually means the API Key is invalid or the temporal arguments (`registreringstid`) are missing.
*   **401/403 (Supabase):** Check your `SUPABASE_KEY`. Ensure you are using the `service_role` key.
*   **0 Shelters Found:** Verify that your Datafordeler user has access to the BBR dataset.

## 6. Architecture Note
This system uses a **Bitemporal** data model query. It asks for records that are currently "valid" in both registration time and effect time. This ensures you only get the active, legal state of a building.