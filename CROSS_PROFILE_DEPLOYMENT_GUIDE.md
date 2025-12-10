# Cross-Profile Session Sync - Deployment Guide

## Pre-Deployment Checklist

### Code Review
- [x] Backend changes reviewed (`app/mongodb_memory.py`, `app/endpoints.py`)
- [x] Frontend changes reviewed (`frontend/src/app/page.tsx`)
- [x] No linter errors
- [x] Backward compatibility verified
- [ ] Security review completed
- [ ] Performance impact assessed

### Testing
- [ ] Unit tests passed (if applicable)
- [ ] Integration tests passed
- [ ] Manual testing in dev environment
- [ ] Cross-profile testing completed
- [ ] Edge case testing completed

### Documentation
- [x] CHANGELOG.md updated
- [x] Technical documentation created
- [x] Architecture diagrams created
- [x] Deployment guide created

## Deployment Steps

### Step 1: Backup Current State

```bash
# Backup MongoDB collection
mongodump --uri="mongodb+srv://..." --db=chatbot --collection=chat_sessions --out=./backup_$(date +%Y%m%d)

# Backup current code
git tag pre-cross-profile-sync-$(date +%Y%m%d)
git push origin --tags
```

### Step 2: Deploy Backend Changes

#### Option A: Docker Deployment

```bash
# Navigate to project directory
cd /path/to/chatbot

# Pull latest changes
git pull origin main

# Rebuild backend container
docker-compose down backend
docker-compose build backend
docker-compose up -d backend

# Verify backend is running
docker-compose ps
docker-compose logs -f backend
```

#### Option B: Manual Deployment

```bash
# Navigate to project directory
cd /path/to/chatbot

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install any new dependencies (if any)
pip install -r requirements.txt

# Restart backend service
sudo systemctl restart chatbot-backend
# or
pm2 restart chatbot-backend
# or manually restart the process
```

#### Verify Backend Deployment

```bash
# Test health endpoint
curl http://localhost:8002/health

# Test session save endpoint (requires auth token)
curl -X POST http://localhost:8002/chat/sessions/save \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test.session.123",
    "title": "Test Session",
    "created_at": 1733702400000,
    "updated_at": 1733702400000,
    "messages": [{"role": "user", "content": "test"}]
  }'

# Test session retrieval endpoint
curl -X GET "http://localhost:8002/chat/sessions/user/test@cloudfuze.com?include_messages=true" \
  -H "Authorization: Bearer YOUR_TEST_TOKEN"
```

### Step 3: Deploy Frontend Changes

#### Option A: Docker Deployment

```bash
# Rebuild frontend container
docker-compose down frontend
docker-compose build frontend
docker-compose up -d frontend

# Verify frontend is running
docker-compose ps
docker-compose logs -f frontend
```

#### Option B: Vercel/Next.js Deployment

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if needed)
npm install

# Build production bundle
npm run build

# Deploy to Vercel
vercel --prod
# or
npm run deploy
```

#### Option C: Manual Static Deployment

```bash
# Build frontend
cd frontend
npm run build

# Copy build output to web server
sudo cp -r .next/standalone/* /var/www/chatbot/
sudo cp -r .next/static /var/www/chatbot/.next/
sudo cp -r public /var/www/chatbot/

# Restart web server
sudo systemctl restart nginx
```

#### Verify Frontend Deployment

1. Open browser and navigate to application URL
2. Open browser console (F12)
3. Look for log messages:
   - `[SESSIONS] Fetching sessions from backend for user: ...`
   - `[SESSIONS] Fetched X sessions from backend`
   - `[SESSIONS] Added X sessions from backend`

### Step 4: Database Verification

```javascript
// Connect to MongoDB
mongosh "mongodb+srv://..."

// Switch to database
use chatbot

// Check if messages field exists in recent sessions
db.chat_sessions.find().limit(5).pretty()

// Verify indexes
db.chat_sessions.getIndexes()

// Count sessions with messages
db.chat_sessions.countDocuments({ messages: { $exists: true } })

// Check average document size
db.chat_sessions.stats()
```

### Step 5: Smoke Testing

#### Test Scenario 1: New Session Creation
1. Login to application in Chrome Profile A
2. Create a new chat session with 3-4 messages
3. Verify session appears in sidebar
4. Check browser console for sync logs
5. Verify in MongoDB that session has messages field

#### Test Scenario 2: Cross-Profile Sync
1. Open Chrome Profile B (different profile, same machine)
2. Login with same Microsoft account
3. Verify session from Profile A appears
4. Click on session and verify messages load correctly
5. Create a new session in Profile B
6. Switch back to Profile A and refresh
7. Verify new session appears in Profile A

#### Test Scenario 3: Message Integrity
1. Open a session with multiple messages
2. Verify all messages display correctly
3. Verify message order is preserved
4. Verify special characters display correctly
5. Verify recommended questions display (if applicable)

### Step 6: Monitoring Setup

#### Application Logs

```bash
# Backend logs
tail -f /var/log/chatbot/backend.log | grep -i "session"

# Frontend logs (browser console)
# Look for [SESSIONS] and [SESSION] prefixed logs

# MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

#### Metrics to Monitor

```javascript
// MongoDB queries to monitor
// 1. Session count growth
db.chat_sessions.countDocuments()

// 2. Average messages per session
db.chat_sessions.aggregate([
  { $project: { messageCount: { $size: "$messages" } } },
  { $group: { _id: null, avgMessages: { $avg: "$messageCount" } } }
])

// 3. Sessions created today
db.chat_sessions.countDocuments({
  created_at: { $gte: new Date(new Date().setHours(0,0,0,0)) }
})

// 4. Most active users
db.chat_sessions.aggregate([
  { $group: { _id: "$user_id", sessionCount: { $sum: 1 } } },
  { $sort: { sessionCount: -1 } },
  { $limit: 10 }
])
```

#### Set Up Alerts

```yaml
# Example alert configuration (adjust for your monitoring system)
alerts:
  - name: session_sync_failure_rate
    condition: error_rate > 5%
    action: notify_team
    
  - name: mongodb_connection_failure
    condition: connection_errors > 0
    action: page_oncall
    
  - name: high_session_fetch_latency
    condition: p95_latency > 2000ms
    action: notify_team
    
  - name: storage_growth
    condition: collection_size_growth > 1GB/day
    action: notify_team
```

## Post-Deployment Verification

### Checklist

- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] Users can login successfully
- [ ] New sessions sync to backend
- [ ] Existing sessions load from backend
- [ ] Cross-profile sync works
- [ ] No duplicate sessions created
- [ ] Performance is acceptable (<2s load time)
- [ ] MongoDB queries are indexed properly
- [ ] No errors in application logs
- [ ] No errors in MongoDB logs

### User Acceptance Testing

1. **Test with Real Users**
   - Select 3-5 beta testers
   - Have them test cross-profile functionality
   - Collect feedback on performance and UX
   - Monitor for any issues

2. **Performance Testing**
   - Measure session fetch time on login
   - Measure session save time after message
   - Check MongoDB query performance
   - Verify no UI lag or freezing

3. **Data Integrity Check**
   - Verify no sessions lost
   - Verify no messages lost
   - Verify no duplicate sessions
   - Verify timestamps are correct

## Rollback Procedure

If critical issues are discovered:

### Step 1: Identify Issue Severity

**Minor Issues** (UI glitches, slow performance):
- Monitor and plan fix for next release
- No immediate rollback needed

**Major Issues** (data loss, authentication failures):
- Proceed with rollback immediately

### Step 2: Rollback Frontend

```bash
# Option A: Docker
docker-compose down frontend
git checkout pre-cross-profile-sync-YYYYMMDD
docker-compose build frontend
docker-compose up -d frontend

# Option B: Vercel
vercel rollback

# Option C: Manual
cd frontend
git checkout pre-cross-profile-sync-YYYYMMDD
npm run build
# Copy build to web server
sudo systemctl restart nginx
```

### Step 3: Rollback Backend

```bash
# Option A: Docker
docker-compose down backend
git checkout pre-cross-profile-sync-YYYYMMDD
docker-compose build backend
docker-compose up -d backend

# Option B: Manual
git checkout pre-cross-profile-sync-YYYYMMDD
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart chatbot-backend
```

### Step 4: Database Cleanup (if needed)

```javascript
// Only if data corruption occurred
// Remove messages field from sessions (optional)
db.chat_sessions.updateMany(
  {},
  { $unset: { messages: "" } }
)

// Restore from backup if necessary
mongorestore --uri="mongodb+srv://..." --db=chatbot --collection=chat_sessions ./backup_YYYYMMDD/chatbot/chat_sessions.bson
```

### Step 5: Notify Users

```
Subject: Service Update - Chat History Feature

Dear CloudFuze Team,

We've temporarily rolled back a recent update to the chat history feature. 
Your chat sessions are safe and will continue to work normally.

We're working on improvements and will redeploy soon.

Thank you for your patience.
```

## Troubleshooting

### Issue: Sessions not syncing to backend

**Symptoms**: New sessions created but not visible in other profiles

**Diagnosis**:
```bash
# Check backend logs
grep "save_session" /var/log/chatbot/backend.log

# Check MongoDB connection
mongosh "mongodb+srv://..." --eval "db.adminCommand('ping')"

# Check API endpoint
curl -X POST http://localhost:8002/chat/sessions/save \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","title":"test","created_at":1733702400000,"messages":[]}'
```

**Solution**:
- Verify MongoDB connection string is correct
- Check authentication tokens are valid
- Verify network connectivity to MongoDB
- Check backend logs for errors

### Issue: Sessions not fetching on login

**Symptoms**: Users only see empty chat history in new profile

**Diagnosis**:
```bash
# Check browser console for errors
# Look for: [SESSIONS] Failed to fetch sessions

# Check API endpoint
curl -X GET "http://localhost:8002/chat/sessions/user/USER_ID?include_messages=true" \
  -H "Authorization: Bearer TOKEN"

# Check backend logs
grep "get_user_sessions" /var/log/chatbot/backend.log
```

**Solution**:
- Verify user_id is correct in request
- Check authentication token is valid
- Verify MongoDB query is working
- Check CORS settings if cross-origin

### Issue: Duplicate sessions appearing

**Symptoms**: Same session appears multiple times in sidebar

**Diagnosis**:
```javascript
// Check for duplicate session_ids in MongoDB
db.chat_sessions.aggregate([
  { $group: { _id: "$session_id", count: { $sum: 1 } } },
  { $match: { count: { $gt: 1 } } }
])

// Check localStorage
// In browser console:
localStorage.getItem('chat_sessions')
```

**Solution**:
- Clear localStorage and re-login
- Remove duplicates from MongoDB
- Fix merge logic in frontend

### Issue: Performance degradation

**Symptoms**: Slow page load, UI lag

**Diagnosis**:
```bash
# Check MongoDB query performance
db.chat_sessions.find({user_id: "user@cloudfuze.com"}).explain("executionStats")

# Check document sizes
db.chat_sessions.aggregate([
  { $project: { size: { $bsonSize: "$$ROOT" } } },
  { $group: { _id: null, avgSize: { $avg: "$size" }, maxSize: { $max: "$size" } } }
])

# Check network latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8002/chat/sessions/user/USER_ID
```

**Solution**:
- Add/verify MongoDB indexes
- Implement pagination for large session counts
- Consider message compression
- Add caching layer

## Success Criteria

Deployment is considered successful when:

✅ All smoke tests pass
✅ No critical errors in logs
✅ User acceptance testing completed
✅ Performance metrics within acceptable range
✅ Cross-profile sync working for all test users
✅ No data loss or corruption
✅ Monitoring and alerts configured
✅ Documentation updated

## Support Contacts

**Technical Issues**:
- Backend: [Backend Team]
- Frontend: [Frontend Team]
- Database: [DBA Team]

**Escalation**:
- On-call Engineer: [Contact]
- Team Lead: [Contact]

## Post-Deployment Tasks

- [ ] Update status page (if applicable)
- [ ] Send deployment notification to team
- [ ] Schedule post-deployment review meeting
- [ ] Document any issues encountered
- [ ] Update runbook with lessons learned
- [ ] Plan next iteration improvements

---

**Deployment Date**: _____________
**Deployed By**: _____________
**Verified By**: _____________
**Status**: ⏳ Pending / ✅ Success / ❌ Rolled Back

**Notes**:
_____________________________________________
_____________________________________________
_____________________________________________

