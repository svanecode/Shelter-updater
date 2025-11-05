# Setup Guide

Complete guide for setting up and running the Shelter Discovery System.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Database Setup](#database-setup)
4. [GitHub Actions Setup](#github-actions-setup)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts

1. **Supabase Account**
   - Sign up at https://supabase.com
   - Create a new project
   - Note your project URL and API keys

2. **Datafordeler Access**
   - Register at https://datafordeler.dk
   - Request access to BBR and DAR APIs
   - Obtain username and password

### Required Software

- Python 3.10 or higher
- Git
- A text editor (VS Code, Sublime, etc.)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/svanecode/Shelter-updater.git
cd Shelter-updater
```

### 2. Install Dependencies

```bash
pip install requests urllib3 python-dotenv
```

Or using requirements file:
```bash
pip install -r requirements.txt  # if you create one
```

### 3. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here

# Datafordeler API Configuration
BBR_API_URL=https://services.datafordeler.dk/BBR/BBRPublic/1/rest
DAR_API_URL=https://services.datafordeler.dk/DAR/DAR/1/rest
DATAFORDELER_USERNAME=your_username
DATAFORDELER_PASSWORD=your_password
```

### 4. Get Credentials

#### Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role key** → `SUPABASE_KEY` (⚠️ Use service role, not anon key)

**Important**: Use the `service_role` key, not the `anon` key. The service role key bypasses Row Level Security (RLS) policies.

#### Datafordeler Credentials

1. Register at https://datafordeler.dk
2. Request API access for:
   - **BBR** (Bygnings- og Boligregistret)
   - **DAR** (Danmarks Adresseregister)
3. You'll receive credentials via email
4. Copy username and password to `.env`

---

## Database Setup

### 1. Create Tables

Run these SQL commands in your Supabase SQL Editor:

#### Shelters Table

```sql
CREATE TABLE IF NOT EXISTS public.sheltersv2 (
    id SERIAL PRIMARY KEY,
    bygning_id VARCHAR(255) UNIQUE NOT NULL,
    shelter_capacity INTEGER,
    anvendelse VARCHAR(255),
    kommunekode VARCHAR(10),
    address TEXT,
    postnummer VARCHAR(10),
    vejnavn TEXT,
    husnummer VARCHAR(50),
    last_checked TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_bygning_id ON public.sheltersv2(bygning_id);
CREATE INDEX IF NOT EXISTS idx_kommunekode ON public.sheltersv2(kommunekode);
CREATE INDEX IF NOT EXISTS idx_postnummer ON public.sheltersv2(postnummer);
```

#### Progress Table

Run the script from `sql/setup_progress_table.sql`:

```sql
-- Create progress tracking table
CREATE TABLE IF NOT EXISTS public.global_progress (
    id SERIAL PRIMARY KEY,
    last_page INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Disable RLS on progress table (not sensitive data)
ALTER TABLE public.global_progress DISABLE ROW LEVEL SECURITY;

-- Insert initial record
INSERT INTO public.global_progress (last_page, last_updated)
SELECT 0, NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.global_progress);

-- Verify
SELECT * FROM public.global_progress;
```

### 2. Verify Table Access

Run this test:
```bash
python tests/test_local_env.py
```

You should see:
```
✅ Supabase connection - PASS
✅ Shelters table access - PASS
```

---

## GitHub Actions Setup

### 1. Fork/Clone Repository

If you haven't already, fork the repository to your GitHub account.

### 2. Configure Secrets

Go to your repository settings:
```
https://github.com/YOUR_USERNAME/Shelter-updater/settings/secrets/actions
```

Add these secrets:

| Secret Name | Value | Where to Find |
|-------------|-------|---------------|
| `SUPABASE_URL` | https://xxx.supabase.co | Supabase Dashboard → Settings → API |
| `SUPABASE_KEY` | eyJ... | Supabase Dashboard → Settings → API (service_role key) |
| `BBR_API_URL` | https://services.datafordeler.dk/BBR/BBRPublic/1/rest | Fixed URL |
| `DAR_API_URL` | https://services.datafordeler.dk/DAR/DAR/1/rest | Fixed URL |
| `DATAFORDELER_USERNAME` | Your username | From Datafordeler registration |
| `DATAFORDELER_PASSWORD` | Your password | From Datafordeler registration |

### 3. Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. Workflows will now run on schedule

### 4. Test Workflow

Trigger a manual run:

1. Go to **Actions** → **Shelter Discovery & Audit**
2. Click **Run workflow**
3. Select **discovery**
4. Click **Run workflow**

Monitor the execution and check logs for any errors.

---

## Testing

### 1. Syntax Check

```bash
python -m py_compile new_shelters_global.py
```

### 2. Logic Tests

Test code logic without API calls:
```bash
python tests/test_shelter_discovery.py
```

Expected output:
```
✅ ALL TESTS PASSED
```

### 3. Environment Tests

Test with real API credentials:
```bash
python tests/test_local_env.py
```

Expected output:
```
✅ env                 : PASS
✅ supabase            : PASS
✅ shelters_table      : PASS
✅ bbr_api             : PASS
✅ dar_api             : PASS
✅ dry_run             : PASS

✅ ALL TESTS PASSED
```

### 4. Credential Test

Quick credential verification:
```bash
bash tests/test_credentials.sh
```

Expected output:
```
✅ SUCCESS! Credentials are correct!
```

### 5. Manual Run

Test the full discovery script locally:
```bash
python new_shelters_global.py
```

**Note**: Ctrl+C to stop after a few pages (it will process 278 pages otherwise).

---

## Troubleshooting

### Common Issues

#### 1. "No global progress record found"

**Cause**: Progress table exists but is empty or has wrong permissions.

**Solution**:
```bash
# Run this SQL in Supabase
ALTER TABLE public.global_progress DISABLE ROW LEVEL SECURITY;

INSERT INTO public.global_progress (last_page, last_updated)
SELECT 0, NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.global_progress);
```

#### 2. "401 Unauthorized" on Supabase

**Cause**: Using `anon` key instead of `service_role` key.

**Solution**:
- Use `service_role` key in `SUPABASE_KEY`
- Find it in Supabase Dashboard → Settings → API

#### 3. "500 Internal Server Error" on BBR API

**Cause**: Wrong Datafordeler credentials.

**Solution**:
- Verify username/password at https://datafordeler.dk
- Check credentials in `.env` match GitHub Secrets exactly
- Test with: `bash tests/test_credentials.sh`

#### 4. API Timeouts

**Cause**: API is slow or overloaded.

**Solution**: This is expected and handled by the script with:
- Exponential backoff (10s → 300s)
- Up to 15 retries
- Progress saved after each page

If persistent:
- Increase `API_SLEEP_TIME` in `new_shelters_global.py`
- Check Datafordeler API status

#### 5. "Missing shelters"

**Cause**: Shelters must meet specific criteria.

**Explanation**: The script only finds shelters with:
- `status` = "6" (in use)
- `byg069Sikringsrumpladser` > 0 (has capacity)

This is intentional - abandoned or inactive shelters are excluded.

#### 6. GitHub Actions Not Running

**Cause**: Workflows not enabled or secrets not set.

**Solution**:
1. Enable workflows in **Actions** tab
2. Verify all 6 secrets are set correctly
3. Check workflow syntax in `.github/workflows/`

#### 7. "Table does not exist"

**Cause**: Database tables not created.

**Solution**: Run the SQL commands in [Database Setup](#database-setup).

---

### Performance Tuning

#### Adjust Batch Size

In `new_shelters_global.py`:
```python
PAGES_PER_BATCH = 278  # Reduce if seeing too many timeouts
API_SLEEP_TIME = 3.0   # Increase if API struggling
```

#### Adjust Schedule

In `.github/workflows/shelter-updater.yml`:
```yaml
schedule:
  - cron: '0 2 * * *'   # 02:00 UTC
  - cron: '0 10 * * *'  # 10:00 UTC
  - cron: '0 18 * * *'  # 18:00 UTC
```

Add more times or reduce frequency as needed.

---

### Getting Help

If you're still stuck:

1. **Check Logs**:
   - GitHub Actions: Check workflow logs
   - Local: Run with verbose output

2. **Verify Credentials**:
   - Run all tests in sequence
   - Check each API endpoint individually

3. **Database Access**:
   - Verify tables exist in Supabase
   - Check RLS policies are disabled on `global_progress`

4. **Create an Issue**:
   - https://github.com/svanecode/Shelter-updater/issues
   - Include error messages and logs
   - DO NOT include credentials or API keys

---

### Additional Resources

- **Datafordeler Documentation**: https://datafordeler.dk/vejledning
- **Supabase Documentation**: https://supabase.com/docs
- **GitHub Actions Documentation**: https://docs.github.com/actions
- **Python Requests Library**: https://requests.readthedocs.io

---

**Setup Complete!** 🎉

Your system should now be:
- ✅ Running locally
- ✅ Deployed to GitHub Actions
- ✅ Processing 3x daily
- ✅ Tracking progress

Monitor at: https://github.com/YOUR_USERNAME/Shelter-updater/actions
