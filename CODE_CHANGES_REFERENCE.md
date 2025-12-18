# Code Changes Reference - Quick Copy-Paste

## 📋 All Changes Made

### 1. Import Timezone in `langfuse_integration.py`

**Line 8 - Import Statement**
```python
# CHANGED FROM
from datetime import datetime

# CHANGED TO
from datetime import datetime, timezone
```

---

### 2. All UTC Timestamps in `langfuse_integration.py`

**Pattern Applied 10 Times Throughout File**

```python
# CHANGED FROM
"timestamp": datetime.now().isoformat()

# CHANGED TO
"timestamp": datetime.now(timezone.utc).isoformat()
```

**Affected Lines:**
- Line 54: `create_trace()` - trace_metadata
- Line 71: `create_trace()` - generation metadata
- Line 140: `log_observation_to_trace()` - span metadata
- Line 165: `create_rag_pipeline_trace()` - trace_metadata
- Line 205: `start_query()` - query_span metadata
- Line 223: `log_retrieval()` - retrieve_span metadata
- Line 231: `log_retrieval()` - embedding span metadata
- Line 246: `start_synthesis()` - synthesize_span metadata
- Line 262: `log_llm_generation()` - generation metadata
- Line 278: `log_response_generation()` - span metadata

---

### 3. Fixed "Last Week" in `/analytics/langfuse/dashboard-summary`

**Lines 3488-3496 in `endpoints.py`**

```python
# CHANGED FROM
elif time_filter == "last_week":
    # Last 7 days
    start_time = now - timedelta(days=7)
    end_time = now

# CHANGED TO
elif time_filter == "last_week":
    # ✅ FIXED: Calendar-based previous week (Monday to Sunday), not rolling 7 days
    # Calculate start of this week (Monday at 00:00:00)
    this_week_start = now - timedelta(days=now.weekday())
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    # Last week starts 7 days before this week (last Monday at 00:00:00)
    start_time = this_week_start - timedelta(days=7)
    # Last week ends at the end of last Sunday (start of this week minus 1 microsecond)
    end_time = this_week_start - timedelta(microseconds=1)
```

---

### 4. Fixed "Last Week" in Legacy `/analytics/langfuse/teams/details`

**Lines 4722-4729 in `endpoints.py`**

```python
# CHANGED FROM
elif time_filter == "last_week":
    # FIX: Calculate previous week (Monday to Sunday), not last 7 days
    now_utc = datetime.utcnow()
    this_week_start = now_utc - timedelta(days=now_utc.weekday())
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = this_week_start - timedelta(days=7)
    end_time = this_week_start - timedelta(microseconds=1)
    max_pages = 20
    request_timeout = 45.0

# CHANGED TO
elif time_filter == "last_week":
    # ✅ FIXED: Calendar-based previous week (Monday to Sunday), not rolling 7 days
    this_week_start = now_utc - timedelta(days=now_utc.weekday())
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = this_week_start - timedelta(days=7)
    end_time = this_week_start - timedelta(microseconds=1)
    max_pages = 20
    request_timeout = 45.0
```

---

### 5. Fixed Timezone Issues in Legacy Endpoint

**Lines 4666-4729 in `endpoints.py`**

```python
# IMPORT SECTION - CHANGED FROM
from datetime import timedelta

# IMPORT SECTION - CHANGED TO
from datetime import timedelta, timezone

# INITIALIZATION - CHANGED FROM
start_time = None
end_time = datetime.utcnow()
max_pages = 30
request_timeout = 60.0

# INITIALIZATION - CHANGED TO
now_utc = datetime.now(timezone.utc)
start_time = None
end_time = now_utc
max_pages = 30
request_timeout = 60.0
```

**Date Parsing - CHANGED FROM:**
```python
start_time = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
end_time = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
```

**Date Parsing - CHANGED TO:**
```python
start_time = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
end_time = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
```

**"Today" Filter - CHANGED FROM:**
```python
elif time_filter == "today":
    start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    max_pages = 10
    request_timeout = 30.0
```

**"Today" Filter - CHANGED TO:**
```python
elif time_filter == "today":
    start_time = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    max_pages = 10
    request_timeout = 30.0
```

**"Yesterday" Filter - CHANGED FROM:**
```python
elif time_filter == "yesterday":
    start_time = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - 
                 timedelta(days=1))
    end_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    max_pages = 10
    request_timeout = 30.0
```

**"Yesterday" Filter - CHANGED TO:**
```python
elif time_filter == "yesterday":
    yesterday = now_utc - timedelta(days=1)
    start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    max_pages = 10
    request_timeout = 30.0
```

**"This Week" Filter - CHANGED FROM:**
```python
elif time_filter == "this_week":
    start_time = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    max_pages = 15
    request_timeout = 45.0
```

**"This Week" Filter - CHANGED TO:**
```python
elif time_filter == "this_week":
    start_time = now_utc - timedelta(days=now_utc.weekday())
    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    max_pages = 15
    request_timeout = 45.0
```

---

## 📊 File Summary

### `app/langfuse_integration.py`
- **Import added:** `timezone` from datetime
- **Timestamp updates:** 10 locations (all changed to UTC)
- **Methods affected:** 8 methods across 2 classes

### `app/endpoints.py`
- **New imports:** `timezone` in legacy endpoint
- **Endpoints fixed:** 
  - `/analytics/langfuse/dashboard-summary` (1 location)
  - `/analytics/langfuse/teams/details` legacy (1 location + timezone fixes)
- **Pattern changes:** 10+ timestamp replacements

---

## ✅ Verification Commands

Run these to verify the changes:

### Check Timezone Imports
```bash
grep -n "from datetime import.*timezone" app/langfuse_integration.py
# Should show: Line 8
```

### Check UTC Timestamps in langfuse_integration.py
```bash
grep -c "datetime.now(timezone.utc)" app/langfuse_integration.py
# Should show: 10 occurrences
```

### Check Last Week Fix
```bash
grep -A 5 "elif time_filter == \"last_week\":" app/endpoints.py | head -20
# Should show calendar-based logic with comments about Monday/Sunday
```

### Check No Naive Timestamps Remain
```bash
grep "datetime.now().isoformat()" app/langfuse_integration.py
# Should show: No matches (all fixed!)
```

### Check No datetime.utcnow() Remains
```bash
grep "datetime.utcnow()" app/endpoints.py
# Should show: No matches in the fixed endpoint (all changed to datetime.now(timezone.utc))
```

---

## 🧪 Testing the Fix

### Quick Test Script
```python
from datetime import datetime, timedelta, timezone

# Test the logic
now = datetime.now(timezone.utc)
this_week_start = now - timedelta(days=now.weekday())
this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
last_week_start = this_week_start - timedelta(days=7)
last_week_end = this_week_start - timedelta(microseconds=1)

print(f"Now: {now}")
print(f"This Week Start: {this_week_start}")
print(f"Last Week Start: {last_week_start}")
print(f"Last Week End: {last_week_end}")

# Verify no overlap
this_week_end = now
assert last_week_end < this_week_start, "ERROR: Week ranges overlap!"
print("✅ No overlap detected!")
```

---

## 📝 Files Modified

1. **`app/langfuse_integration.py`** - 10 timestamp changes + 1 import
2. **`app/endpoints.py`** - 2 last_week fixes + timezone consistency fixes

---

## 🎯 Key Points

1. **All timestamps are now UTC** - No timezone ambiguity
2. **Last Week is now calendar-based** - Monday to Sunday of previous week
3. **No overlap with This Week** - Clean date boundaries
4. **Backward compatible** - No API signature changes
5. **Frontend unchanged** - Already correct, no changes needed

---

## 🚀 Deployment Notes

- ✅ No database migrations needed
- ✅ No API breaking changes
- ✅ No frontend changes needed
- ✅ Backward compatible with existing code
- ✅ Safe to deploy to production
