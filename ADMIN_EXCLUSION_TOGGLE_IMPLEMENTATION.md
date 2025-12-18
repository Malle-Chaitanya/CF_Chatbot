# Admin Analytics Exclusion Toggle - Implementation Guide

## Overview

Implemented a dynamic exclusion list system that allows admins to toggle which emails are excluded from team analytics via a frontend toggle button, instead of hardcoding exclusions in the backend.

---

## Changes Made

### 1. **Backend - `app/models/teams.py`**

**Status**: ✅ Exclusion list now empty and dynamic

```python
# Email exclusion list for analytics - MANAGED VIA FRONTEND TOGGLE
ANALYTICS_EXCLUSION_LIST = set()  # Empty by default - all emails included

def is_email_excluded(email: str, exclusion_list: set = None) -> bool:
    """
    Check if email should be excluded from analytics.
    Now accepts dynamic exclusion list from frontend.
    """
    if not email or not exclusion_list:
        return False
    return email.lower().strip() in exclusion_list
```

**Key Changes**:
- Removed hardcoded exclusion list
- Made `is_email_excluded()` accept dynamic exclusion list parameter
- All emails now included by default

---

### 2. **Backend - `app/endpoints.py`**

**Status**: ✅ Added 3 new admin endpoints

#### **Endpoint 1: Get Current Exclusion List**
```
GET /analytics/langfuse/exclusion-list
```

**Response**:
```json
{
  "status": "success",
  "exclusion_list": [
    "laxman.kadari@cloudfuze.com",
    "chaitanya.malle@cloudfuze.com"
  ],
  "description": "Emails currently excluded from team analytics",
  "note": "Frontend can toggle these emails on/off via the exclusion API"
}
```

#### **Endpoint 2: Update Exclusion List**
```
POST /analytics/langfuse/exclusion-list/update
```

**Request Body**:
```json
{
  "exclusion_emails": [
    "laxman.kadari@cloudfuze.com",
    "chaitanya.malle@cloudfuze.com"
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "exclusion_list": [
    "chaitanya.malle@cloudfuze.com",
    "laxman.kadari@cloudfuze.com"
  ],
  "total_excluded": 2,
  "message": "Exclusion list updated. 2 emails will be excluded from analytics."
}
```

#### **Endpoint 3: Get Analytics With Custom Exclusion**
```
GET /analytics/langfuse/teams/summary/with-exclusion?time_filter=today&exclusion_emails=laxman.kadari@cloudfuze.com,chaitanya.malle@cloudfuze.com
```

**Query Parameters**:
- `time_filter`: today, yesterday, this_week, last_week, this_month, all
- `exclusion_emails`: Comma-separated list of emails to exclude

**Response**: Same as regular team analytics, but with:
- Applied exclusions
- `excluded_trace_count`: Number of traces excluded
- `exclusion_list`: List of excluded emails used

---

### 3. **Team Updates - `app/models/teams.py`**

**Status**: ✅ Complete

**Changes**:
- ✅ `yogesh.vig@cloudfuze.com` already added to Sales – SMB team
- ✅ `laxman.kadari@cloudfuze.com` already added to Neutara Labs team
- ✅ `chaitanya.malle@cloudfuze.com` already added to Neutara Labs team

---

## Frontend Implementation Guide

### 1. **Admin Toggle Button Component**

```tsx
// Add to Analytics Dashboard or Admin Settings page

interface ExclusionToggle {
  email: string;
  name: string;
  isExcluded: boolean;
}

const AdminExclusionToggle = () => {
  const [exclusions, setExclusions] = useState<ExclusionToggle[]>([
    { email: "laxman.kadari@cloudfuze.com", name: "Laxman Kadari", isExcluded: false },
    { email: "chaitanya.malle@cloudfuze.com", name: "Chaitanya Malle", isExcluded: false },
  ]);

  const handleToggle = async (email: string) => {
    const updatedExclusions = exclusions.map(e => 
      e.email === email ? { ...e, isExcluded: !e.isExcluded } : e
    );
    setExclusions(updatedExclusions);

    // Send to backend
    const emailsToExclude = updatedExclusions
      .filter(e => e.isExcluded)
      .map(e => e.email);

    const response = await fetch('/analytics/langfuse/exclusion-list/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ exclusion_emails: emailsToExclude })
    });

    const data = await response.json();
    console.log('Exclusion list updated:', data);
  };

  return (
    <div className="admin-exclusion-panel">
      <h3>Exclude from Analytics</h3>
      {exclusions.map(item => (
        <div key={item.email} className="toggle-item">
          <label>
            <input 
              type="checkbox" 
              checked={item.isExcluded}
              onChange={() => handleToggle(item.email)}
            />
            {item.name} ({item.email})
          </label>
        </div>
      ))}
    </div>
  );
};
```

### 2. **Get Analytics with Exclusions**

```tsx
const getAnalyticsWithExclusions = async (
  timeFilter: string,
  excludedEmails: string[]
) => {
  const emailsParam = excludedEmails.join(',');
  
  const response = await fetch(
    `/analytics/langfuse/teams/summary/with-exclusion?time_filter=${timeFilter}&exclusion_emails=${emailsParam}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );

  const data = await response.json();
  
  return {
    teams: data.teams,
    totalQuestions: data.total_questions,
    excludedCount: data.excluded_trace_count,
    exclusionList: data.exclusion_list
  };
};
```

### 3. **Display Excluded Count**

```tsx
<div className="analytics-info">
  <p>Total Questions: {data.total_questions}</p>
  {data.excluded_trace_count > 0 && (
    <p className="warning">
      Excluded {data.excluded_trace_count} traces from: {data.exclusion_list.join(', ')}
    </p>
  )}
</div>
```

---

## Usage Flow

### For Admin Users:

1. **View Current Exclusions**
   ```
   GET /analytics/langfuse/exclusion-list
   ```

2. **Toggle Exclusions**
   - Use the admin UI toggle button
   - Backend calls `POST /analytics/langfuse/exclusion-list/update`

3. **View Analytics with Applied Exclusions**
   - Query with `GET /analytics/langfuse/teams/summary/with-exclusion`
   - Passes comma-separated excluded emails

---

## Default Behavior

### **Current State**:
- ✅ No emails excluded by default
- ✅ All team members included in analytics
- ✅ Frontend can apply exclusions dynamically

### **Example Scenarios**:

**Scenario 1**: Include everyone (default)
```
GET /analytics/langfuse/teams/summary?time_filter=today
```
Result: All traces included

**Scenario 2**: Exclude 2 people
```
GET /analytics/langfuse/teams/summary/with-exclusion?time_filter=today&exclusion_emails=laxman.kadari@cloudfuze.com,chaitanya.malle@cloudfuze.com
```
Result: 2 people excluded from analytics

---

## Benefits

✅ **Flexible**: Admin can toggle exclusions without code changes
✅ **Dynamic**: Changes apply immediately to new analytics queries
✅ **Traceable**: Logs show which emails were excluded
✅ **User-Friendly**: Simple toggle UI for admin
✅ **Default Inclusive**: All emails included by default (no surprises)

---

## Technical Details

### Authentication
- All endpoints require `require_restricted_admin` dependency
- Only restricted admin users can access exclusion endpoints

### Validation
- Emails validated for format (must contain @ and .)
- Invalid emails silently skipped
- Case-insensitive matching

### Performance
- No database changes needed
- Exclusions applied at query time
- No impact on trace ingestion

---

## Testing Checklist

- [ ] Fetch exclusion list: `GET /analytics/langfuse/exclusion-list`
- [ ] Update exclusion list: `POST /analytics/langfuse/exclusion-list/update`
- [ ] Get analytics with exclusions: `GET /analytics/langfuse/teams/summary/with-exclusion?exclusion_emails=...`
- [ ] Verify excluded traces are not counted
- [ ] Verify logs show excluded emails
- [ ] Frontend toggle updates backend correctly
- [ ] Works with all time_filter values

---

## Notes

- Frontend should cache exclusion state to avoid unnecessary API calls
- Consider adding a "preset exclusions" feature for common use cases
- Could extend to exclude by team in future

