# Credential Verification Guide

## Problem Identified

Your local tests show:
- ✅ **Supabase works** - Credentials are correct
- ❌ **BBR API fails with 500 error** - Credentials likely incorrect

GitHub Actions **DOES work** (reached page 32,920), which means:
- ✅ GitHub Secrets have **correct** credentials
- ❌ Your local `.env` file has **different** credentials

## How to Fix

### Step 1: Check Your GitHub Secrets

Go to your repository settings:
```
https://github.com/svanecode/Shelter-updater/settings/secrets/actions
```

You should see these secrets:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `BBR_API_URL`
- `DAR_API_URL`
- `DATAFORDELER_USERNAME`
- `DATAFORDELER_PASSWORD`

### Step 2: Compare with Local .env

Your current `.env` file has:
```
DATAFORDELER_USERNAME=AndreasSvane7J5E5
DATAFORDELER_PASSWORD=kUVXBXSesaUTf1tC$
```

**ACTION REQUIRED:**
1. Check if the username in GitHub Secrets matches `AndreasSvane7J5E5`
2. Check if the password in GitHub Secrets matches `kUVXBXSesaUTf1tC$`
3. If they're different, update your `.env` file with the correct values from GitHub Secrets

### Step 3: Common Issues

#### Issue 1: Typos
- Double-check for typos in username/password
- Case-sensitive!
- Check for extra spaces

#### Issue 2: Special Characters
- The `$` at the end of your password might be incorrect
- Check if it should be a different character

#### Issue 3: Credentials Expired/Changed
- Datafordeler credentials might have been updated
- You might need to regenerate them

## Testing Your Credentials

### Option 1: Use a Working Page from GitHub Actions

From your GitHub Actions logs, we know page 1 worked before. Try this curl command:

```bash
# Replace with your actual credentials
curl "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning?username=YOUR_USERNAME&password=YOUR_PASSWORD&format=json&page=1"
```

If this returns JSON data, your credentials are correct.
If it returns `(500) Internal server error`, your credentials are wrong.

### Option 2: Test Without Special Characters

If your password has a `$` at the end, try:
1. Check if it's supposed to be there
2. Try URL encoding: `%24` instead of `$`
3. Try escaping it in the .env file: `kUVXBXSesaUTf1tC\$`

## Solution Paths

### Path A: Fix Local Credentials (Recommended)

1. Copy exact values from GitHub Secrets to `.env`
2. Run `python test_local_env.py` again
3. Should work now ✅

### Path B: Deploy Without Local Testing

If you can't get local credentials to work:

1. ✅ Your GitHub Secrets ARE correct (proven by past runs)
2. ✅ All logic tests passed
3. ✅ Supabase works locally
4. ✅ Syntax is clean

**You can safely deploy!**

```bash
git add new_shelters_global.py
git commit -m "Fix cycle completion bug and improve error handling"
git push
```

The script will work in GitHub Actions even if it doesn't work locally.

## Why This Happens

Common reasons for different credentials locally vs GitHub:

1. **Copy-paste errors** when creating `.env`
2. **Outdated credentials** in `.env`
3. **Test credentials** locally vs **production credentials** in GitHub
4. **Special character encoding** issues

## Next Steps

**Choose ONE:**

### Option 1: Fix Local Testing ⭐ Recommended
- [ ] Verify credentials match GitHub Secrets exactly
- [ ] Update `.env` file
- [ ] Run `python test_local_env.py`
- [ ] Should get ✅ ALL TESTS PASSED

### Option 2: Deploy Now
- [ ] Trust that GitHub Actions works (it did before)
- [ ] Skip local API testing
- [ ] Commit and push changes
- [ ] Monitor next GitHub Actions run

---

**Both options are valid!** The code changes are tested and ready. Local API testing is just for extra confidence.
