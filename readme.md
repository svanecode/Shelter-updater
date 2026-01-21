# Shelter Discovery & Sync System

Automated system for discovering and auditing civil defense shelters across Denmark using official government data sources (Datafordeler).

## Overview

This system synchronizes the Danish Building and Dwelling Register (BBR) with a Supabase database to maintain an up-to-date registry of civil defense shelters.

**Key Features:**
- **Efficient GraphQL Sync:** Directly queries for valid shelters (`status: 6`), reducing scan time from hours to minutes.
- **Differential Updates:** Only updates records that have changed, minimizing database load.
- **Address Enrichment:** Automatically fetches address details from the Danish Address Register (DAR) for new or stale records.
- **Soft Deletes:** Marks shelters as deleted if they disappear from the official register, and restores them if they return.

## System Architecture

### Data Sources
1.  **BBR (Bygnings- og Boligregistret)** via GraphQL:
    *   Source of truth for building status and shelter capacity.
2.  **DAR (Danmarks Adresseregister)** via REST:
    *   Source for human-readable addresses (Street, Number, Zip).

### Database
*   **Supabase (PostgreSQL):** Stores the `sheltersv2` table.

### Schedule
The synchronization runs automatically via **GitHub Actions** daily at **04:00 UTC**.

## Setup & Usage

### Prerequisites
*   Python 3.10+
*   Supabase Project
*   Datafordeler API Account (Tjenestebruger)

### Environment Variables
Create a `.env` file with the following:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
DATAFORDELER_API_KEY=your_api_key
```

Optional tuning variables:

```env
ADDRESS_REFRESH_DAYS=90
PAGE_SIZE=500
BATCH_SIZE=200
GRAPHQL_PAGE_SLEEP=0.2
DAR_SLEEP_TIME=0.1
MAX_GRAPHQL_RETRIES=8
GRAPHQL_RETRY_BASE_SLEEP=5
SAFE_THRESHOLD=500
MIN_DELETE_COVERAGE=0.8
```

### Running Locally

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure `requests`, `python-dotenv` are installed)*

2.  **Run the sync:**
    ```bash
    python sync_shelters_graphql.py
    ```

## Logic Details

1.  **State Loading:** Fetches all known `bygning_id`s from Supabase to build a local state map.
2.  **GraphQL Query:** Iterates through BBR pages for all buildings with `status: 6` (Shelter).
3.  **Comparison:**
    *   **New ID:** Fetch Address -> Insert.
    *   **Capacity Change:** Update Capacity -> Update.
    *   **Stale Address (>90 days):** Re-fetch Address -> Update.
    *   **Seen in BBR:** Updates `last_seen_at` even if unchanged.
    *   **Deleted Flagged:** If found again -> Restore (Un-delete).
    *   **Missing from BBR:** If an ID in DB is not found in BBR -> Soft Delete (set `deleted` timestamp).

## License
MIT
