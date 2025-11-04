# Local Testing Setup Guide

## Prerequisites

You need to create a `.env` file with your actual API credentials to run local tests.

## Step 1: Create .env File

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` and add your actual credentials:

```bash
# Edit with your preferred editor
nano .env
# or
code .env
# or
vi .env
```

## Step 2: Fill in Credentials

Your `.env` file should look like this:

```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Datafordeler API Configuration
BBR_API_URL=https://services.datafordeler.dk/BBR/BBRPublic/1/rest
DAR_API_URL=https://services.datafordeler.dk/DAR/DAR/1/rest
DATAFORDELER_USERNAME=your_actual_username
DATAFORDELER_PASSWORD=your_actual_password
```

### Where to Find Your Credentials:

1. **Supabase URL & Key**:
   - Go to your Supabase project dashboard
   - Click on "Settings" → "API"
   - Copy the "Project URL" and "anon/public key"

2. **Datafordeler Username & Password**:
   - These are provided by Datafordeler when you register
   - Should be in your GitHub Secrets as `DATAFORDELER_USERNAME` and `DATAFORDELER_PASSWORD`

3. **API URLs**:
   - BBR API: `https://services.datafordeler.dk/BBR/BBRPublic/1/rest`
   - DAR API: `https://services.datafordeler.dk/DAR/DAR/1/rest`
   - These should stay as shown above

## Step 3: Run Tests

Once your `.env` file is configured:

### Test 1: Logic Tests (No API calls)
```bash
python test_shelter_discovery.py
```
This tests the code logic without making API calls.

### Test 2: Environment & API Tests (With real API)
```bash
python test_local_env.py
```
This tests:
- ✅ Environment variables are set
- ✅ Supabase database connection
- ✅ Access to sheltersv2 table
- ✅ BBR API connection (Datafordeler)
- ✅ DAR API connection (Datafordeler)
- ✅ Dry run (2 pages, no database writes)

### Test 3: Full Syntax Check
```bash
python -m py_compile new_shelters_global.py
```

## Expected Test Results

### If Everything Works:
```
============================================================
TEST SUMMARY
============================================================
  env                 : ✅ PASS
  supabase            : ✅ PASS
  shelters_table      : ✅ PASS
  bbr_api             : ✅ PASS
  dar_api             : ✅ PASS
  dry_run             : ✅ PASS

============================================================
✅ ALL TESTS PASSED
============================================================

Your script is ready to run in production!
You can safely deploy to GitHub Actions.
```

### If API is Slow/Timing Out:
You might see:
```
  Testing: https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning
  Fetching page 1... (this may take up to 60s)
  ❌ FAILED - Request timed out after 60s
  This is the same timeout issue from your GitHub Actions logs
```

This confirms the API connection issue. The script now handles this with:
- Exponential backoff (10s, 20s, 40s, 80s, 160s, 300s)
- Up to 15 retries before giving up
- Saves progress so it can resume

## Troubleshooting

### Issue: "MISSING VARIABLES"
**Problem**: `.env` file doesn't exist or is empty
**Solution**: Create `.env` file using the template above

### Issue: "Connection error" to Supabase
**Problem**: Wrong URL or API key
**Solution**: Double-check your Supabase credentials in dashboard

### Issue: "Connection error" to Datafordeler
**Problem**: Wrong username/password or API is down
**Solution**:
1. Verify your Datafordeler credentials
2. Check if API is accessible: https://datafordeler.dk/
3. Try again later if API is slow/down

### Issue: "Request timed out"
**Problem**: Datafordeler API is slow (same as GitHub Actions issue)
**Solution**: This is expected! The script now handles this:
- Retries with exponential backoff
- Continues from where it stopped
- Will try again on next run

## Security Note

**IMPORTANT**: Never commit your `.env` file to git!

The `.gitignore` file is already configured to ignore `.env`, but double-check before committing:

```bash
git status
# Should NOT show .env file
```

If you accidentally add it:
```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
```

## Next Steps

After all tests pass locally:

1. ✅ Commit the changes to `new_shelters_global.py`
2. ✅ Push to GitHub
3. ✅ Monitor the next GitHub Actions run
4. ✅ Verify it starts from page 1 (new cycle)
5. ✅ Check logs for successful processing

## Files in This Test Suite

- `test_shelter_discovery.py` - Logic tests (no API calls)
- `test_local_env.py` - Environment & API tests (real credentials)
- `.env.example` - Template for your credentials
- `LOCAL_TEST_SETUP.md` - This file
- `TESTING_SUMMARY.md` - Detailed test results
- `NEXT_RUN_FLOWCHART.md` - What happens on next run
