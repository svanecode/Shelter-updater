# Shelter Discovery System

A comprehensive system for discovering and monitoring shelters across Denmark using the BBR (Building and Dwelling Register) API.

## Overview

This system uses a **global page-based strategy** to process all buildings across Denmark without municipality-specific filtering. It processes pages in batches and tracks progress globally to ensure all pages are processed within a **30-day cycle**.

## Key Features

- **Global Strategy**: Processes all buildings across Denmark without municipality boundaries
- **30-Day Cycles**: Completes full processing of all pages every 30 days
- **Automated Processing**: Runs twice daily via GitHub Actions
- **Progress Tracking**: Monitors completion status and provides detailed reports
- **Duplicate Prevention**: Prevents duplicate shelter entries
- **Audit System**: Validates and maintains data quality

## Architecture

### Global Strategy
- **Batch Size**: 834 pages per run
- **Frequency**: Twice daily (02:00 and 14:00 UTC)
- **Cycle Duration**: 30 days
- **Total Pages**: ~50,000 estimated pages across Denmark
- **Completion Rate**: ~1,668 pages per day

### Processing Flow
1. **Page Processing**: Processes pages sequentially across all of Denmark
2. **Progress Tracking**: Updates global progress table with current page
3. **Cycle Management**: Resets to page 0 every 30 days
4. **Duplicate Checking**: Prevents duplicate shelter entries
5. **Data Validation**: Ensures data quality and completeness

## Files

### Core Scripts
- `new_shelters_global.py` - Main shelter discovery script (global strategy)
- `shelter_audit.py` - Data validation and audit script
- `monitor_global_progress.py` - Progress monitoring and reporting

### Utilities
- `calculate_optimal_batch.py` - Calculates optimal batch sizes for different frequencies

### GitHub Actions
- `.github/workflows/shelter-updater.yml` - Main automation workflow
- `.github/workflows/progress-monitor.yml` - Weekly progress monitoring

## Setup

### Environment Variables
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
BBR_API_URL=your_bbr_api_url
DAR_API_URL=your_dar_api_url
DATAFORDELER_USERNAME=your_username
DATAFORDELER_PASSWORD=your_password
```

### Database Tables
The system uses these Supabase tables:
- `shelters` - Main shelter data
- `global_progress` - Global processing progress

## Usage

### Manual Execution
```bash
# Run shelter discovery
python new_shelters_global.py

# Check progress
python monitor_global_progress.py

# Run audit
python shelter_audit.py

# Calculate optimal batch sizes
python calculate_optimal_batch.py
```

### GitHub Actions
The system runs automatically via GitHub Actions:
- **Shelter Discovery**: Twice daily at 02:00 and 14:00 UTC
- **Shelter Audit**: Weekly on Sundays at 03:00 UTC
- **Progress Monitoring**: Weekly on Sundays at 10:00 UTC

### Manual Trigger
You can manually trigger workflows via GitHub Actions with these options:
- `discovery` - Run shelter discovery
- `audit` - Run shelter audit
- `report` - Generate progress report

## Monitoring

### Progress Tracking
The system tracks:
- Current page being processed
- Pages completed in current cycle
- Time since last update
- Estimated completion time
- Cycle status (in progress/complete)

### Performance Metrics
- **Processing Rate**: ~1,668 pages per day
- **Cycle Completion**: Every 30 days
- **Batch Efficiency**: 834 pages per run
- **Total Coverage**: All of Denmark

## Configuration

### Batch Size Optimization
The current configuration processes 834 pages per run, twice daily, to complete all pages within 30 days. You can adjust this based on:

- **Daily Processing**: 1,667 pages per run
- **Twice Daily**: 834 pages per run (current)
- **Every 6 Hours**: 417 pages per run
- **Every 4 Hours**: 278 pages per run

Use `calculate_optimal_batch.py` to find the optimal configuration for your needs.

## Benefits

### Efficiency
- **Global Processing**: No municipality boundaries or complex tracking
- **Even Distribution**: Consistent workload across time
- **Scalable**: Easy to adjust batch sizes and frequencies

### Reliability
- **Progress Persistence**: Survives interruptions and restarts
- **Duplicate Prevention**: Robust duplicate checking
- **Data Validation**: Comprehensive audit system

### Maintainability
- **Simple Logic**: Straightforward page-based processing
- **Clear Monitoring**: Easy to track progress and performance
- **Flexible Configuration**: Easy to adjust for different requirements

## Troubleshooting

### Common Issues
1. **API Rate Limits**: Reduce batch size if hitting rate limits
2. **Processing Delays**: Increase batch size or frequency
3. **Database Errors**: Check Supabase connection and permissions
4. **Progress Stuck**: Verify global_progress table exists and is accessible

### Performance Tuning
- Use `calculate_optimal_batch.py` to find optimal settings
- Monitor progress with `monitor_global_progress.py`
- Adjust batch sizes based on API performance
- Consider different scheduling frequencies

## Future Enhancements

- **Adaptive Batch Sizing**: Adjust batch size based on API performance
- **Real-time Monitoring**: Web dashboard for progress tracking
- **Multi-region Processing**: Parallel processing across regions
- **Advanced Analytics**: Detailed performance and coverage metrics
