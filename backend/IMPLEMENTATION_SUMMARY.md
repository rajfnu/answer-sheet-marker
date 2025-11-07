# Implementation Summary: Cost Optimization & Observability Features

## Completed Features

### 1. ✅ File Hash-Based Caching
**Location**: `backend/src/answer_marker/storage/persistent_storage.py`

**Features**:
- SHA-256 hash-based file deduplication
- Automatic cache lookup before processing
- Prevents re-analysis of identical PDFs
- **Cost Savings**: Eliminates duplicate Claude API calls for same files

**How it works**:
```python
# When uploading a marking guide:
file_hash = compute_file_hash(file_path)
cached_guide_id = check_cache(file_hash)
if cached_guide_id:
    # Return cached guide, NO API calls needed!
    return load_marking_guide(cached_guide_id)
else:
    # Process new guide and cache it
    process_and_save(guide, file_hash)
```

### 2. ✅ Persistent Storage
**Location**: `backend/src/answer_marker/storage/persistent_storage.py`

**Features**:
- Marking guides persist across server restarts
- Reports persist across server restarts
- JSON metadata for fast lookups
- Pickle serialization for Python objects
- Automatic directory structure creation

**Storage Structure**:
```
backend/data/storage/
├── marking_guides/
│   ├── guide_abc123.pkl
│   └── guide_def456.pkl
├── reports/
│   ├── report_xyz789.pkl
│   └── report_uvw012.pkl
├── cache/
└── metadata.json
```

**Benefits**:
- Data survives server restarts
- Fast startup (loads from disk)
- No need to re-process on deployment

### 3. ✅ Cost Estimation & Token Usage Tracking
**Location**: `backend/src/answer_marker/observability/cost_tracker.py`

**Features**:
- Real-time token counting
- Per-operation cost tracking
- Per-guide cost tracking
- Per-report cost tracking
- Session-wide cost summary
- Support for all Claude models with accurate pricing

**Pricing Database** (as of 2024):
- Claude Sonnet 4.5: $3/MTok input, $15/MTok output
- Claude 3 Opus: $15/MTok input, $75/MTok output
- Claude 3 Sonnet: $3/MTok input, $15/MTok output
- Claude 3 Haiku: $0.25/MTok input, $1.25/MTok output

**Usage Example**:
```python
from answer_marker.observability.cost_tracker import cost_tracker

# Record usage
cost_tracker.record_usage(
    operation_name="analyze_question_1",
    input_tokens=1500,
    output_tokens=600,
    model="claude-sonnet-4-5-20250929",
    context_id="guide_abc123",
    context_type="guide"
)

# Get cost summary
summary = cost_tracker.get_session_summary()
# {
#   "total_cost_usd": 0.0165,
#   "total_tokens": 2100,
#   "num_calls": 1,
#   ...
# }
```

## In Progress / To Be Integrated

### 4. ⏳ LangFuse Observability Integration
**Planned Location**: `backend/src/answer_marker/observability/langfuse_integration.py`

**Features** (to be implemented):
- Automatic trace logging for all LLM calls
- Visual dashboards in LangFuse UI
- Performance monitoring
- Token usage visualization
- Cost analytics over time
- Error tracking and debugging

**Integration Points**:
- Wrap all Claude API calls
- Track document processing pipeline
- Monitor agent performance
- Log evaluation results

### 5. ⏳ Model Evaluation Framework
**Planned Location**: `backend/src/answer_marker/evaluation/`

**Features** (to be implemented):
- A/B testing different models
- Compare marking quality across models
- Cost vs. quality trade-offs
- Automated evaluation metrics
- Ground truth comparison
- Inter-rater reliability scores

## Integration with Marking Service

The marking service needs to be updated to:
1. Use `PersistentStorage` instead of in-memory dicts
2. Check cache before processing files
3. Record token usage with `CostTracker`
4. Save guides and reports to persistent storage
5. Load existing data on startup

**Key Changes Needed**:
```python
class MarkingService:
    def __init__(self):
        self.storage = PersistentStorage(Path("data/storage"))
        self.cost_tracker = cost_tracker

        # Load existing data on startup
        self.marking_guides, self.reports = self.storage.load_all_to_memory()

    async def upload_marking_guide(self, file_path, filename):
        # Check cache first
        cached_guide_id = self.storage.check_cache(file_path)
        if cached_guide_id:
            logger.info(f"Using cached guide: {cached_guide_id}")
            return cached_guide_id, self.marking_guides[cached_guide_id]

        # Process new guide
        guide_id, guide = await self._process_new_guide(file_path)

        # Save to persistent storage
        self.storage.save_marking_guide(guide_id, guide, file_path)

        return guide_id, guide
```

## API Enhancements Needed

### New Endpoints:
1. `GET /api/v1/costs/session` - Get session-wide cost summary
2. `GET /api/v1/costs/guide/{guide_id}` - Get costs for specific guide
3. `GET /api/v1/costs/report/{report_id}` - Get costs for specific report
4. `GET /api/v1/cache/stats` - Cache hit/miss statistics
5. `GET /api/v1/storage/stats` - Storage usage statistics

### Enhanced Responses:
Add cost information to existing responses:
```json
{
  "guide_id": "guide_abc123",
  "title": "Math Assessment",
  "cost_breakdown": {
    "processing_cost_usd": 0.0165,
    "total_tokens": 21000,
    "num_api_calls": 10
  },
  "cached": false
}
```

## Environment Variables Needed

Add to `.env`:
```bash
# Storage
STORAGE_DIR=data/storage

# LangFuse (optional)
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# Cost Tracking
ENABLE_COST_TRACKING=true
COST_TRACKING_LOG_FILE=data/costs.json
```

## Benefits Summary

### Cost Savings:
- **Caching**: Eliminates duplicate processing (saves 100% on repeated files)
- **Visibility**: Know exactly how much each operation costs
- **Optimization**: Identify expensive operations to optimize

### Operational Benefits:
- **Persistence**: No data loss on restart
- **Observability**: Full visibility into system behavior
- **Debugging**: Track down issues with detailed logs
- **Analytics**: Understand usage patterns

### Developer Experience:
- **Transparency**: Clear cost breakdown for every operation
- **Monitoring**: Real-time dashboard with LangFuse
- **Testing**: Compare models easily
- **Confidence**: Know the system state at all times

## Next Steps

1. **Install Dependencies**:
   ```bash
   cd backend
   poetry install
   ```

2. **Add Credits to Anthropic Account**:
   - Go to https://console.anthropic.com/settings/plans
   - Add credits to continue testing

3. **Update Marking Service**:
   - Integrate `PersistentStorage`
   - Add cache checks
   - Record costs
   - Implement LangFuse tracing

4. **Test Features**:
   - Upload same file twice → should use cache
   - Check cost summary endpoint
   - Verify persistence after restart

5. **Deploy with Docker**:
   - Add storage volume mount
   - Configure environment variables
   - Test full-stack deployment

## Cost Estimation Example

**Scenario**: Marking 100 answer sheets with 10 questions each

**Without Caching**:
- Upload marking guide: 10 questions × 1500 tokens/question = 15,000 tokens
- Mark 100 sheets: 100 × (10 questions × 2000 tokens) = 2,000,000 tokens
- **Total Cost**: ~$30-40 (depending on model)

**With Caching**:
- Upload marking guide once: 15,000 tokens (subsequent uploads = 0 tokens)
- Mark 100 sheets: 2,000,000 tokens
- **Total Cost**: ~$30-40 (first time), then $0 for guide re-uploads
- **Savings**: 100% on duplicate guide uploads

## Files Created

1. ✅ `backend/src/answer_marker/storage/persistent_storage.py` (320 lines)
2. ✅ `backend/src/answer_marker/storage/__init__.py`
3. ✅ `backend/src/answer_marker/observability/cost_tracker.py` (230 lines)
4. ⏳ `backend/src/answer_marker/observability/langfuse_integration.py` (pending)
5. ⏳ `backend/src/answer_marker/observability/__init__.py` (pending)
6. ⏳ `backend/src/answer_marker/evaluation/` (pending)
7. ⏳ Updated `backend/src/answer_marker/api/services/marking_service.py` (pending)

## Dependencies Added

- `langfuse ^2.50.0` - Observability and tracing
- `xxhash ^3.4.1` - Fast file hashing (alternative to hashlib, can use either)

Status: ✅ Dependencies locked with poetry lock
