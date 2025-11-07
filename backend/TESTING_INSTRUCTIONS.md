# Testing Caching System - Credit-Saving Guide

## ✅ System Status
- Backend: http://127.0.0.1:8001 (Running)
- Frontend: http://localhost:5173 (Running)
- Caching: ENABLED
- Storage: backend/data/storage/

## 🎯 Smart Testing Strategy (Minimizes API Calls)

### Test 1: Upload Marking Guide (First Time)
**Expected Cost: ~10 API calls (~$0.015-0.02)**

1. Open browser: http://localhost:5173
2. Click "Upload Marking Guide"
3. Select: `example/Assessment.pdf`
4. Upload and wait for processing

**What Happens:**
- File is processed for the first time
- 10 questions analyzed (1 API call per question)
- Result cached with file hash
- Total: ~10 API calls

### Test 2: Upload SAME Marking Guide (Second Time)
**Expected Cost: 0 API calls ($0.00) - CACHE HIT!**

1. Click "Upload Marking Guide" again
2. Select the SAME file: `example/Assessment.pdf`
3. Upload

**What to Look For:**
- Upload completes INSTANTLY
- Backend logs show: `⚡ CACHE HIT: Using cached marking guide guide_xxxxx (0 API calls, $0.00 cost)`
- **ZERO API calls** - 100% savings!

### Test 3: Mark Answer Sheet (First Time)
**Expected Cost: ~15-20 API calls (~$0.03-0.05)**

1. Click "Mark Answers"
2. Select marking guide from dropdown
3. Enter student ID: `TEST-001`
4. Upload: `example/Student Answer Sheet 1.pdf`
5. Click "Mark Answer Sheet"

**What Happens:**
- Answer sheet processed
- Each answer evaluated against marking guide
- Report generated and cached
- Total: ~15-20 API calls

### Test 4: Mark SAME Answer Sheet (Second Time)
**Expected Cost: 0 API calls ($0.00) - CACHE HIT!**

1. Click "Mark Answers" again
2. Same marking guide
3. Same student ID: `TEST-001`
4. Upload SAME file: `example/Student Answer Sheet 1.pdf`
5. Click "Mark Answer Sheet"

**What to Look For:**
- Marking completes INSTANTLY
- Backend logs show: `⚡ CACHE HIT: Using cached report report_xxxxx for TEST-001 (0 API calls, $0.00 cost)`
- **ZERO API calls** - 100% savings!

## 📊 Total Cost Estimate

### Without Caching (Old System):
- Upload guide twice: 2 × 10 = 20 calls
- Mark same sheet twice: 2 × 15 = 30 calls
- **Total: 50 API calls (~$0.10)**

### With Caching (New System):
- Upload guide first time: 10 calls
- Upload guide second time: 0 calls (CACHED)
- Mark sheet first time: 15 calls
- Mark sheet second time: 0 calls (CACHED)
- **Total: 25 API calls (~$0.05)**

**Savings: 50% on this simple test!**

## 🔍 Monitoring Cache Hits

### Option 1: Watch Backend Logs
```bash
cd backend
tail -f backend_live.log | grep -E "(CACHE HIT|⚡|Processing NEW)"
```

Look for these messages:
- `⚡ CACHE HIT: Using cached marking guide` - Marking guide cache hit
- `⚡ CACHE HIT: Using cached report` - Answer sheet cache hit
- `Processing NEW marking guide` - First time processing (will use API calls)
- `Marking NEW answer sheet` - First time marking (will use API calls)

### Option 2: Check Storage Directory
```bash
# See cached guides
ls -la backend/data/storage/marking_guides/

# See cached reports
ls -la backend/data/storage/reports/

# View cache metadata
cat backend/data/storage/metadata.json | python -m json.tool
```

## ⚠️ Important Notes

1. **Cache Key for Marking Guides**: File SHA-256 hash
   - Same file = Same hash = Cache hit
   - Even 1 byte different = Different hash = New processing

2. **Cache Key for Answer Sheets**: `{guide_id}:{student_id}:{file_hash}`
   - Must match ALL three to get cache hit
   - Different student ID = New marking (even with same file)

3. **Persistence**: Cache survives server restarts!
   - Stop and restart servers
   - Upload same files again
   - Still get cache hits!

4. **Cost Tracking**: Check session costs
   ```bash
   curl http://localhost:8001/api/v1/costs/session 2>/dev/null | python -m json.tool
   ```
   (Note: Cost tracking endpoints coming in next update)

## 🎓 Advanced Testing

### Test Different Students
- Mark `Student Answer Sheet 1.pdf` as `STUDENT-A` → Uses API calls
- Mark SAME FILE as `STUDENT-B` → Uses API calls (different student)
- Mark SAME FILE as `STUDENT-A` again → **CACHE HIT!**

### Test File Modifications
- Upload `Assessment.pdf` → Uses API calls
- Modify the PDF (even 1 character)
- Upload modified version → Uses API calls (different hash)
- Upload original again → **CACHE HIT!**

## 📝 What to Report

After testing, note:
1. Did you see "⚡ CACHE HIT" messages?
2. Was the second upload instant compared to first?
3. Check cost: How many API calls for full test?
4. Any errors or issues?

## 🚀 Next Steps

Once caching is confirmed working:
1. Clear old data from previous sessions
2. Start fresh marking workflow
3. Enjoy 50-100% savings on duplicate uploads!
