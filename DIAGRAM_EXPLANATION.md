# Visual Explanation of the "Last Week" Filter Fix

## 🎯 The Problem

### ❌ BEFORE: Rolling 7-Day Window (WRONG)

```
TODAY = Wednesday, Dec 17, 2025

Timeline:
  Mon Dec 8    Tue Dec 9  ... Wed Dec 17 (TODAY)
  |------------|-----------|
       └─────────────────────────────────┘ (7 days back from now)
             "last_week" range (WRONG!)
         
  Mon Dec 15   Tue Dec 16   Wed Dec 17 (TODAY)
  └─────────────────────┘
      "this_week" range

PROBLEM: 
- Both filters include data from Dec 15-17!
- Overlapping date ranges cause incorrect totals
- Users see almost the same data for both filters
```

### ✅ AFTER: Calendar-Based Week Ranges (CORRECT)

```
TODAY = Wednesday, Dec 17, 2025

Timeline:
  
  Mon Dec 8    Sun Dec 14    Mon Dec 15    Wed Dec 17 (TODAY)
  ├──────────────────────────┤├──────────────────────────┤
       "last_week"                "this_week"
       (Previous Calendar      (Current Calendar
        Week: Mon-Sun)         Week: Mon-today)

SOLUTION:
✅ No overlap!
✅ Clean date boundaries
✅ Matches user expectations ("last week" = previous calendar week)
```

---

## 📊 Data Range Examples

### Example 1: Wednesday Afternoon

```
Current Time: Dec 17, 2025 at 2:30 PM UTC

This Week:
├─ Start: Dec 15, 2025 at 00:00:00 UTC (Monday)
└─ End:   Dec 17, 2025 at 2:30:00 PM UTC (Now)

Last Week:
├─ Start: Dec 8, 2025 at 00:00:00 UTC (Monday)
└─ End:   Dec 14, 2025 at 23:59:59.999999 UTC (Sunday)
```

### Example 2: Sunday Evening

```
Current Time: Dec 14, 2025 at 11:50 PM UTC

This Week:
├─ Start: Dec 8, 2025 at 00:00:00 UTC (Monday)
└─ End:   Dec 14, 2025 at 11:50:00 PM UTC (Now)

Last Week:
├─ Start: Dec 1, 2025 at 00:00:00 UTC (Monday)
└─ End:   Dec 7, 2025 at 23:59:59.999999 UTC (Sunday)
```

### Example 3: Monday Morning

```
Current Time: Dec 15, 2025 at 8:00 AM UTC

This Week:
├─ Start: Dec 15, 2025 at 00:00:00 UTC (Monday - today)
└─ End:   Dec 15, 2025 at 8:00:00 AM UTC (Now)

Last Week:
├─ Start: Dec 8, 2025 at 00:00:00 UTC (Monday)
└─ End:   Dec 14, 2025 at 23:59:59.999999 UTC (Sunday)
```

---

## 🔧 The Technical Fix

### Code Logic

```python
# Step 1: Get current time in UTC
now = datetime.now(timezone.utc)

# Step 2: Find Monday of current week
# weekday() returns: Monday=0, Tuesday=1, ..., Sunday=6
days_since_monday = now.weekday()
monday_of_this_week = now - timedelta(days=days_since_monday)

# Step 3: Reset to midnight of that Monday
monday_at_midnight = monday_of_this_week.replace(
    hour=0, minute=0, second=0, microsecond=0
)

# Step 4: Calculate last week
last_week_start = monday_at_midnight - timedelta(days=7)  # Previous Monday
last_week_end = monday_at_midnight - timedelta(microseconds=1)  # Just before Monday midnight
```

### Example Calculation

```
Now: Dec 17, 2025 at 14:30 UTC (Wednesday)

Step 1: now.weekday() = 2 (Wednesday is day 2)
Step 2: Monday of this week = Dec 17 - 2 days = Dec 15
Step 3: Reset to midnight = Dec 15 at 00:00:00
Step 4: Last week = Dec 15 - 7 days = Dec 8 (previous Monday)
        Last week end = Dec 15 - 1 microsecond = Dec 14 at 23:59:59.999999

Result:
  This Week: Dec 15 00:00:00 → Dec 17 14:30:00
  Last Week: Dec 8 00:00:00 → Dec 14 23:59:59.999999
```

---

## ⏰ Timezone Importance

### ❌ BEFORE: Naive Timestamps

```python
"timestamp": datetime.now().isoformat()
# Result: "2025-12-17T14:30:00" (NO TIMEZONE INFO!)

Problem:
- In NYC: interpreted as EST (UTC-5)
- In London: interpreted as GMT (UTC+0)
- In Tokyo: interpreted as JST (UTC+9)
- Week boundaries become INCONSISTENT across regions!
```

### ✅ AFTER: UTC Timestamps

```python
"timestamp": datetime.now(timezone.utc).isoformat()
# Result: "2025-12-17T14:30:00+00:00" or "2025-12-17T14:30:00Z"

Benefit:
- Same everywhere on Earth
- Monday 00:00:00 UTC = Monday 00:00:00 UTC globally
- No ambiguity, no timezone drift
```

---

## 📈 Impact on Analytics

### Query Count Comparison

**Before Fix (Rolling 7 days):**
```
Dec 8  (Mon):  5 queries  |
Dec 9  (Tue):  3 queries  |
Dec 10 (Wed):  7 queries  |
Dec 11 (Thu):  4 queries  |
Dec 12 (Fri):  6 queries  |
Dec 13 (Sat):  2 queries  |
Dec 14 (Sun):  1 query    | ─ "Last Week" (rolling): 28 queries
Dec 15 (Mon):  8 queries  |   ⚠️ INCLUDES Dec 15!
Dec 16 (Tue):  6 queries  |
Dec 17 (Wed):  5 queries  | ─ "This Week": 25 queries
Total from Dec 8-17: 47   ⚠️ 9 queries overlap (Dec 15-17)!

User sees: "Last Week (28) vs This Week (25)"
Reality: They're looking at different data, confusing!
```

**After Fix (Calendar weeks):**
```
Dec 8  (Mon):  5 queries  |
Dec 9  (Tue):  3 queries  |
Dec 10 (Wed):  7 queries  |
Dec 11 (Thu):  4 queries  |
Dec 12 (Fri):  6 queries  |
Dec 13 (Sat):  2 queries  |
Dec 14 (Sun):  1 query    | ─ "Last Week": 28 queries (Dec 8-14)
Dec 15 (Mon):  8 queries  |   ✅ EXCLUDES Dec 15!
Dec 16 (Tue):  6 queries  |
Dec 17 (Wed):  5 queries  | ─ "This Week": 19 queries (Dec 15-17)
Total:         47         ✅ 0 queries overlap! Clean separation!

User sees: "Last Week (28) vs This Week (19)"
Reality: Clear, non-overlapping data! 🎉
```

---

## 🎯 Verification Checklist

After deploying the fix, verify:

### ✅ Data Integrity
- [ ] "Last Week" total ≠ "This Week" total
- [ ] "Last Week" + "This Week" ≈ "All" (for the past 14 days)
- [ ] Same totals after page refresh

### ✅ Date Boundaries
- [ ] "This Week" starts on current week's Monday
- [ ] "Last Week" ends on current week's Monday minus 1 microsecond
- [ ] No data overlap between filters

### ✅ Timezone Consistency
- [ ] All timestamps in Langfuse have `+00:00` or `Z` suffix
- [ ] Analytics same for users in different timezones
- [ ] Monday/Sunday boundaries are consistent globally

### ✅ API Responses
- [ ] Log shows: `start_time=2025-12-08T00:00:00+00:00` (UTC marker present)
- [ ] Log shows: `end_time=2025-12-14T23:59:59.999999+00:00`
- [ ] No naive timestamps in responses

---

## 📚 Related Standards

This fix aligns with industry standards:

| Platform | "Last Week" Means | Starts | Ends |
|----------|-----------------|--------|------|
| **Google Analytics** | Previous calendar week | Last Monday 00:00 UTC | Last Sunday 23:59 UTC |
| **Datadog** | Previous calendar week | Last Monday 00:00 UTC | Last Sunday 23:59 UTC |
| **Our Fix** | Previous calendar week | Last Monday 00:00 UTC | Last Sunday 23:59 UTC |
| ❌ Old Code | Last 7 days (rolling) | Now - 7 days | Now |

---

## 🎉 Summary

The fix changes the behavior from:
- ❌ **"Show me the last 7 days of data"** (rolling, overlapping)
- ✅ **"Show me the previous calendar week"** (clean, non-overlapping)

This is what users expect and what Langfuse queries correctly!
