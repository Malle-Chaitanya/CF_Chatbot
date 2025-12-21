# Team Analytics & Leaderboard System

## Quick Start

### Access the Dashboard
- URL: `http://localhost:3000/admin/teams`
- Requires admin login
- Displays team analytics with leaderboard

### What You'll See
1. **Summary Stats** - Total teams, active teams, total questions, average
2. **🏆 Leaderboard** - Teams ranked by questions with medals for top 3
3. **Teams Grid** - Card view of all teams
4. **Team Details Modal** - Click any team to see member breakdown

---

## Features

### 1. Date Range Filtering
```
- Calendar-based picker (start date → end date)
- Apply button to fetch data
- Reset button to clear selection
- Cache: 1-hour storage of results
```

### 2. Team Leaderboard
```
- Ranked by total questions (highest first)
- 🥇 🥈 🥉 medals for top 3 teams
- Shows: Total Q's, Unique Q's, Active Members, Average
- Click row to view team details
- Hover effects for interactivity
```

### 3. Email-Based Team Assignment
```
- User activity matched to team by email
- Case-insensitive lookup
- 19 teams total
- Unassigned for unknown emails
```

### 4. Team Details Modal
```
- Team lead information
- Total questions & unique questions
- Active members ratio
- List of all members with stats
```

---

## Team Structure

### 19 Teams (138+ members)

**Development:**
- Content (12)
- Messaging & Email (20)
- CF Manage (6)
- QA (10)
- Neutara Labs (9)
- Infra (6)

**Business:**
- Marketing (11)
- Pre-Sales (3)
- BD (9)

**Manufacturing:**
- M1 (6), M2 (6), M3 (6), M4 (6), M5 (4)

**Sales:**
- Sales Ops (5), Sales SMB (7), Sales ENT (3), Sales AM (7)

**Support:**
- HR (5)

---

## Files & Documentation

### Code Files
- `app/models/teams.py` - Team structure & helper functions
- `frontend/src/app/admin/teams/page.tsx` - Leaderboard UI

### Documentation
- `TEAMS_UPDATE_SUMMARY.md` - Overview of changes
- `LEADERBOARD_TESTING_GUIDE.md` - Complete testing guide
- `TEAMS_COMPLETE_LIST.md` - Full team directory with all members
- `LEADERBOARD_VISUAL_GUIDE.md` - Visual walkthrough
- `IMPLEMENTATION_COMPLETE.md` - Project completion details
- `README_TEAMS_LEADERBOARD.md` - This file

---

## How It Works

### Data Flow
```
Langfuse Traces
     ↓
Extract user_email from metadata
     ↓
Match email to team member
     ↓
Aggregate by team
     ↓
Calculate statistics
     ↓
Display in leaderboard
```

### Email Matching
```python
from app.models.teams import get_team_by_member_email

# Example
team = get_team_by_member_email("santosh@cloudfuze.com")
# Returns: "Content"
```

### Caching System
```typescript
// 1 hour cache duration
const CACHE_DURATION_MS = 60 * 60 * 1000;

// Same date range = instant load
// Different date range = new API call
```

---

## Testing the Leaderboard

### Quick Test (5 minutes)
1. Navigate to `http://localhost:3000/admin/teams`
2. Select a date range (e.g., today)
3. Click "Apply"
4. Verify leaderboard shows 19 teams sorted by questions
5. Check top 3 have medals (🥇🥈🥉)

### Full Test (20 minutes)
See `LEADERBOARD_TESTING_GUIDE.md` for:
- All test scenarios
- Data accuracy checks
- Performance testing
- Error handling
- Debugging tips

---

## API Endpoint

### GET /analytics/langfuse/teams/summary

**Parameters:**
```
start_date: YYYY-MM-DD
end_date: YYYY-MM-DD
Authorization: Bearer {token}
```

**Response:**
```json
{
  "status": "success",
  "total_teams": 19,
  "total_active_teams": 15,
  "total_questions_overall": 2500,
  "teams": [
    {
      "team_name": "Content",
      "lead": "Santosh Chintalapelli",
      "lead_email": "santosh@cloudfuze.com",
      "member_count": 12,
      "active_members_count": 8,
      "color": "#3B82F6",
      "total_questions": 450,
      "unique_questions": 120,
      "top_questions": [...]
    }
  ]
}
```

---

## Troubleshooting

### Issue: Leaderboard blank
- [ ] Check if admin logged in
- [ ] Check browser console (F12)
- [ ] Check backend logs
- [ ] Verify date range has data

### Issue: Wrong team assignment
- [ ] Check email format in Langfuse
- [ ] Verify email in team structure
- [ ] Run: `get_team_by_member_email(email)`

### Issue: Slow loading
- [ ] Check Langfuse API response times
- [ ] Try narrower date range
- [ ] Check browser network tab

---

## Performance

| Metric | Target | Expected |
|--------|--------|----------|
| First Load | < 5s | 3-4s |
| Cached Load | < 1s | 0.5s |
| Row Click | instant | instant |
| API Response | < 30s | 10-20s |

---

## Browser Compatibility

- ✓ Chrome/Edge (latest)
- ✓ Firefox (latest)
- ✓ Safari (latest)
- ✓ Mobile browsers
- ✓ Tablet browsers

---

## Deployment Checklist

- [ ] All linter checks pass
- [ ] No console errors
- [ ] Leaderboard renders correctly
- [ ] Email matching verified
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Testing complete
- [ ] Ready to deploy

---

## Key Improvements

### From Previous Version
- ✅ All 19 teams with accurate emails
- ✅ Leaderboard ranking system
- ✅ Medal awards for top 3
- ✅ Better table layout
- ✅ Hover effects
- ✅ Click to details modal
- ✅ Caching for performance
- ✅ Complete documentation

---

## Next Features (Future)

- [ ] Export to CSV
- [ ] Month-over-month trends
- [ ] Individual member leaderboards
- [ ] Team comparison charts
- [ ] Time-series analytics
- [ ] Department-level rollup
- [ ] Custom team filters

---

## Support

### Documentation
- `TEAMS_COMPLETE_LIST.md` - Team/member lookup
- `LEADERBOARD_TESTING_GUIDE.md` - Testing help
- `LEADERBOARD_VISUAL_GUIDE.md` - UI walkthrough

### Debug Commands
```bash
# Check teams.py syntax
python -m py_compile app/models/teams.py

# Test email lookup
python -c "from app.models.teams import get_team_by_member_email; print(get_team_by_member_email('santosh@cloudfuze.com'))"

# Check backend API
curl -H "Authorization: Bearer {token}" http://localhost:8000/analytics/langfuse/teams/summary
```

---

## Version Info
- **Version:** 1.0
- **Date:** 2025-12-16
- **Status:** ✅ Ready for Testing & Deployment
- **Teams:** 19
- **Total Members:** 138+

---

## Contact & Questions

For questions about:
- **Team structure** → See `TEAMS_COMPLETE_LIST.md`
- **Testing** → See `LEADERBOARD_TESTING_GUIDE.md`
- **UI/UX** → See `LEADERBOARD_VISUAL_GUIDE.md`
- **Implementation** → See `IMPLEMENTATION_COMPLETE.md`

---

**Happy testing! 🎉**

