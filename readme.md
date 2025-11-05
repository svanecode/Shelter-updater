# Shelter Discovery & Audit System

Automated system for discovering and auditing civil defense shelters across Denmark using official government data sources.

## Overview

This system continuously scans the Danish Building and Dwelling Register (BBR) to maintain an up-to-date database of all civil defense shelters in Denmark. It tracks shelter locations, capacities, and status changes over time.

### Key Features

- **Automated Discovery**: Scans 50,000+ building records to find shelters
- **Progress Tracking**: Resumes from last processed position
- **Error Recovery**: Exponential backoff and retry logic for API stability
- **Scheduled Execution**: Runs 3x daily via GitHub Actions
- **Audit System**: Weekly verification of existing shelter data
- **Data Integration**: Combines BBR (building) and DAR (address) data

## System Architecture

### Data Sources

- **BBR (Bygnings- og Boligregistret)**: Building and dwelling register
  - Building usage codes
  - Shelter capacity (`byg069Sikringsrumpladser`)
  - Construction details

- **DAR (Danmarks Adresseregister)**: Danish address register
  - Street addresses
  - Postal codes
  - Geographic coordinates

### Database

Supabase PostgreSQL database with two main tables:
- `sheltersv2`: Shelter records with full details
- `global_progress`: Tracking scan progress across 30-day cycles

### Scheduling

Runs **3 times daily** at:
- 02:00 UTC (04:00 CET) - Night processing
- 10:00 UTC (12:00 CET) - Midday processing
- 18:00 UTC (20:00 CET) - Evening processing

Each run processes **278 pages** (~18 minutes) with 3-second intervals between API requests.

**Complete cycle**: ~60 days to scan all 50,000 pages, then restarts.

## Quick Start

### Prerequisites

- Python 3.10+
- Supabase account
- Datafordeler API credentials ([register here](https://datafordeler.dk))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/svanecode/Shelter-updater.git
   cd Shelter-updater
   ```

2. **Install dependencies**
   ```bash
   pip install requests urllib3 python-dotenv
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run locally** (optional)
   ```bash
   python new_shelters_global.py
   ```

For detailed setup instructions, see [docs/SETUP.md](docs/SETUP.md).

## Project Structure

```
Shelter-updater/
├── README.md                       # This file
├── new_shelters_global.py          # Main discovery script
├── shelter_audit.py                # Weekly audit script
├── monitor_global_progress.py      # Progress monitoring
├── docs/
│   └── SETUP.md                    # Detailed setup guide
├── tests/
│   ├── test_shelter_discovery.py   # Logic tests
│   ├── test_local_env.py           # Environment tests
│   └── test_credentials.sh         # Credential verification
├── sql/
│   └── setup_progress_table.sql    # Database initialization
└── .github/workflows/
    ├── shelter-updater.yml         # Main workflow (3x daily)
    └── progress-monitor.yml        # Progress monitoring
```

## Configuration

### Environment Variables

Required in `.env` or GitHub Secrets:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key

# Datafordeler APIs
BBR_API_URL=https://services.datafordeler.dk/BBR/BBRPublic/1/rest
DAR_API_URL=https://services.datafordeler.dk/DAR/DAR/1/rest
DATAFORDELER_USERNAME=your_username
DATAFORDELER_PASSWORD=your_password
```

### Adjustable Parameters

In `new_shelters_global.py`:

```python
PAGES_PER_BATCH = 278      # Pages per run
API_SLEEP_TIME = 3.0       # Seconds between requests
CYCLE_DAYS = 30            # Days before restarting scan
REQUEST_TIMEOUT = 60       # API request timeout
MAX_RUNTIME_SECONDS = 18000 # 5 hours max per run
```

## Usage

### GitHub Actions (Automated)

The system runs automatically 3x daily. Monitor at:
```
https://github.com/svanecode/Shelter-updater/actions
```

### Manual Execution

**Discovery**:
```bash
python new_shelters_global.py
```

**Audit**:
```bash
python shelter_audit.py
```

**Check Progress**:
```bash
python monitor_global_progress.py
```

### Testing

```bash
# Test logic (no API calls)
python tests/test_shelter_discovery.py

# Test environment (uses real APIs)
python tests/test_local_env.py

# Test credentials
bash tests/test_credentials.sh
```

## How It Works

### Discovery Process

1. **Initialize**: Load existing shelter IDs from database
2. **Resume**: Get last processed page from `global_progress`
3. **Scan**: Fetch building records page by page from BBR API
4. **Filter**: Identify shelters (status=6, capacity>0)
5. **Enrich**: Fetch address data from DAR API
6. **Store**: Save new shelters to database
7. **Track**: Update progress after each page
8. **Repeat**: Continue until batch complete

### Error Handling

- **Timeouts**: Exponential backoff (10s → 300s max)
- **Rate Limits**: 60-second backoff on 429 errors
- **Connection Issues**: Retry with increasing delays
- **Max Retries**: 15 consecutive errors before stopping
- **Progress Saving**: After every page to enable resume

### Cycle Management

- **30-day cycles**: Complete rescan every month
- **Automatic restart**: Begins new cycle when >30 days since last run
- **Incremental progress**: Picks up exactly where it stopped

## Monitoring

### GitHub Actions Dashboard

View run history, logs, and status:
```
https://github.com/svanecode/Shelter-updater/actions
```

### Supabase Dashboard

Check data and progress:
```
https://supabase.com/dashboard/project/irafzkpgqxdhsahoddxr
```

**Tables**:
- `sheltersv2`: All discovered shelters
- `global_progress`: Current scan position

### Progress Metrics

```bash
python monitor_global_progress.py
```

Output shows:
- Current cycle date
- Last processed page
- Pages remaining
- Estimated completion time
- Completion percentage

## Troubleshooting

### Common Issues

**"No global progress record found"**
- Solution: Run `sql/setup_progress_table.sql` in Supabase

**API timeouts**
- Expected behavior with exponential backoff
- Check Datafordeler API status
- Consider increasing `API_SLEEP_TIME`

**403/401 errors**
- Verify Datafordeler credentials
- Check service role key for Supabase
- Ensure GitHub Secrets are set correctly

**Missing shelters**
- System finds only shelters with:
  - `status` = "6" (in use)
  - `byg069Sikringsrumpladser` > 0 (has capacity)

See [docs/SETUP.md](docs/SETUP.md) for detailed troubleshooting.

## Performance

### Current Metrics

- **Request rate**: 20 requests/minute (3-second intervals)
- **Pages per run**: 278 pages (~18 minutes)
- **Daily progress**: 834 pages (278 × 3 runs)
- **Cycle duration**: ~60 days for 50,000 pages
- **Success rate**: ~99% with retry logic

### Optimization

The 3x daily schedule provides:
- ✅ Better API stability (shorter sessions)
- ✅ Distributed load across different times
- ✅ 3x more retry opportunities per day
- ✅ Faster recovery from failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project uses public Danish government data sources:
- [Datafordeler](https://datafordeler.dk) - Official data distribution platform
- All data is public and free to use per Danish open data regulations

## Support

- **Issues**: [GitHub Issues](https://github.com/svanecode/Shelter-updater/issues)
- **Datafordeler Support**: https://datafordeler.dk/support
- **Supabase Docs**: https://supabase.com/docs

## Acknowledgments

- **Data Sources**: Danish Agency for Data Supply and Infrastructure (SDFI)
- **APIs**: Datafordeler.dk platform
- **Database**: Supabase
- **CI/CD**: GitHub Actions

---

**Status**: ✅ Production Ready | Last Updated: November 2025
