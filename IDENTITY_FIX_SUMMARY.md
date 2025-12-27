# Identity Fix Summary

## Problem
Users were sometimes logged in as "USER" with missing chat history because:
- `user_id` could be `None` or inconsistent
- Name defaulted to `"User"` when missing
- `conversation_id` fell back to `session_id` instead of `user_id`
- This created multiple storage buckets for the same person

## Solution: Strict Identity Validation

### ✅ Rule 1: Email is Mandatory
- **Fail fast** if email is missing (no silent fallbacks)
- All auth paths now validate email presence

### ✅ Rule 2: Email = user_id (Always)
- Use email as the single source of truth for `user_id`
- Ensures consistent identity across all sessions
- Chat history always stored under the same key

### ✅ Rule 3: conversation_id = user_id (Never session_id)
- Removed fallback to `session_id`
- All conversations use `user_id` (email) as the key
- Prevents chat history fragmentation

### ✅ Rule 4: No "User" Default
- Removed default name fallback
- Extract name from email if displayName missing
- Better than silent "User" default

## Files Modified

1. **app/endpoints.py**
   - OAuth callback: Enforce email, use email as user_id
   - `require_auth()`: Validate session identity, use email as user_id
   - Chat endpoints: Remove session_id fallback, use user_id only
   - Unsafe JWT fallback: Use email as user_id

2. **app/auth.py**
   - `get_current_user()`: Validate session identity, migrate old sessions
   - `_get_current_user_from_token()`: Use email as user_id

3. **app/session_store.py**
   - `create_session()`: Validate email, ensure user_id = email

4. **scripts/cleanup_bad_sessions.py** (NEW)
   - MongoDB cleanup script to remove corrupted sessions

## Next Steps

1. **Deploy the fixes** to your environment

2. **Run cleanup script** (ONCE):
   ```bash
   python scripts/cleanup_bad_sessions.py
   ```
   This removes sessions with:
   - Missing email
   - Empty email
   - Email = "USER"
   - user_id != email (inconsistent)

3. **Monitor logs** for:
   - `[AUTH] Session user_id mismatch` warnings (old sessions being migrated)
   - `[AUTH] ⚠️ Invalid user_id` errors (should not happen after fix)

## Testing

After deployment, verify:
- ✅ Users can log in successfully
- ✅ Chat history appears correctly
- ✅ No "USER" names in UI
- ✅ All sessions have consistent user_id = email

## Notes

- Old sessions will be automatically migrated (user_id updated to email) on first access
- New sessions will always have user_id = email from creation
- Chat history stored under email will be consistent going forward

