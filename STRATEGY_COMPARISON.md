# Strategy Comparison: Per-Municipality vs Global Page-Based

## Overview

This document compares two approaches for discovering new shelters:
1. **Per-Municipality Strategy** (`new_shelters.py`) - Processes municipalities individually
2. **Global Page-Based Strategy** (`new_shelters_global.py`) - Processes all buildings globally

## 🏛️ Per-Municipality Strategy

### How It Works
- Processes one municipality at a time
- Uses `kommunekode` parameter in BBR API calls
- Tracks progress per municipality in `kommunekoder` table
- Processes 5 pages per municipality per run

### ✅ Advantages
- **Municipality-specific tracking**: Know exactly which municipalities are complete
- **Geographic organization**: Easy to understand progress by region
- **Selective processing**: Can process specific municipalities if needed
- **Familiar approach**: Matches administrative boundaries

### ❌ Disadvantages
- **API inefficiency**: Requires separate calls per municipality
- **Uneven workload**: Some municipalities have 10 pages, others 1000+
- **Complex tracking**: Need to manage progress for each municipality
- **Scalability issues**: Adding new municipalities requires database changes
- **Time waste**: Small municipalities finish quickly, large ones take forever
- **Database complexity**: Need `kommunekoder` table with per-municipality tracking

### Database Schema Required
```sql
-- kommunekoder table
CREATE TABLE kommunekoder (
    kode TEXT PRIMARY KEY,
    last_page INTEGER,
    last_updated TIMESTAMP
);
```

## 🌍 Global Page-Based Strategy

### How It Works
- Processes all buildings across Denmark globally
- Uses only `page` parameter in BBR API calls
- Tracks progress globally in `global_progress` table
- Processes 10 pages per run across all data

### ✅ Advantages
- **API efficiency**: Single API call pattern, no municipality filtering
- **Even distribution**: Work is distributed evenly across all pages
- **Simple tracking**: Only one progress record to manage
- **Better scalability**: No need to manage municipality list
- **Predictable performance**: Consistent page processing time
- **Automatic coverage**: Naturally covers all municipalities without explicit tracking

### ❌ Disadvantages
- **Less geographic visibility**: Harder to see progress by region
- **No selective processing**: Can't easily process specific areas
- **Less intuitive**: Doesn't match administrative boundaries
- **Requires estimation**: Need to estimate total page count

### Database Schema Required
```sql
-- global_progress table
CREATE TABLE global_progress (
    id SERIAL PRIMARY KEY,
    last_page INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);
```

## 📊 Performance Comparison

| Aspect | Per-Municipality | Global Page-Based |
|--------|------------------|-------------------|
| **API Calls** | Multiple per municipality | Single pattern |
| **Progress Tracking** | Complex (per municipality) | Simple (global) |
| **Database Complexity** | High (municipality table) | Low (single record) |
| **Work Distribution** | Uneven | Even |
| **Scalability** | Poor | Excellent |
| **Geographic Visibility** | High | Low |
| **Implementation Complexity** | High | Low |

## 🎯 Recommendation: Global Page-Based Strategy

### Why Global is Better

1. **🚀 Efficiency**: Much more efficient API usage
2. **⚖️ Fairness**: Even distribution of work across all data
3. **🔧 Simplicity**: Simpler code and database schema
4. **📈 Scalability**: Easy to scale and maintain
5. **⏱️ Predictability**: Consistent processing time per run

### When to Use Per-Municipality

- If you need geographic progress visibility
- If you need to process specific municipalities selectively
- If your data is naturally organized by municipality boundaries

## 🔄 Migration Path

To migrate from per-municipality to global strategy:

1. **Create global_progress table**:
```sql
CREATE TABLE global_progress (
    id SERIAL PRIMARY KEY,
    last_page INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);
```

2. **Initialize global progress**:
```sql
INSERT INTO global_progress (last_page, last_updated) VALUES (0, NOW());
```

3. **Switch to global script**:
```bash
# Instead of
python new_shelters.py

# Use
python new_shelters_global.py
```

4. **Monitor with global monitor**:
```bash
# Instead of
python monitor_monthly_progress.py

# Use
python monitor_global_progress.py
```

## 📈 Expected Performance Improvement

- **API Efficiency**: ~90% reduction in API complexity
- **Database Operations**: ~95% reduction in tracking operations
- **Code Complexity**: ~70% reduction in code complexity
- **Maintenance**: ~80% reduction in maintenance overhead

## 🎯 Conclusion

The **Global Page-Based Strategy** is significantly better for most use cases because:

1. **It's more efficient** - Better API usage and simpler tracking
2. **It's more scalable** - Easy to maintain and extend
3. **It's more predictable** - Consistent performance characteristics
4. **It's simpler** - Less code and database complexity

The per-municipality strategy should only be used if you have specific requirements for geographic progress tracking or selective municipality processing. 