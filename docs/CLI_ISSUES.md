# CLI Known Issues and Workarounds

## Issue: Typer 0.9.x Rich Integration Bug

### Summary

The CLI has a known issue with Typer 0.9.x's Rich integration that prevents options from accepting values when Rich formatting is enabled.

### Error Messages

- `TypeError: Parameter.make_metavar() missing 1 required positional argument: 'ctx'` (help rendering)
- `Option '--option-name' does not take a value` (option parsing)

### Root Cause

Typer's `rich_utils.py` module calls `param.make_metavar()` without passing the required `ctx` argument in version 0.9.x. A monkey-patch was implemented to fix help rendering, but it interferes with option value parsing.

### Status

- ✅ Help rendering: FIXED (via monkey-patch in `commands.py`)
- ❌ Option value parsing: NOT FIXED (monkey-patch causes side effects)

### Workarounds

#### Option 1: Use Python Scripts Directly (Recommended)

Instead of using the CLI, call the marking system directly via Python:

```python
import asyncio
from pathlib import Path
from answer_marker.config import settings
from answer_marker.llm.factory import create_llm_client_from_config
from answer_marker.llm.compat import LLMClientCompat
from answer_marker.document_processing import DocumentProcessor
from answer_marker.core.orchestrator import create_orchestrator_agent
# ... import other agents and models

async def mark_papers():
    # Initialize LLM client
    llm_client = create_llm_client_from_config(settings)
    client = LLMClientCompat(llm_client)

    # Initialize processors and agents
    doc_processor = DocumentProcessor(client)
    orchestrator = create_orchestrator_agent(client, agents)

    # Process marking guide
    marking_guide_data = await doc_processor.process_marking_guide(
        Path("example/Assessment.pdf")
    )
    marking_guide = MarkingGuide(**marking_guide_data)

    # Process answer sheet
    answer_sheet_data = await doc_processor.process_answer_sheet(
        Path("example/Student Answer Sheet 1.pdf"),
        [q.id for q in marking_guide.questions]
    )
    answer_sheet = AnswerSheet(**answer_sheet_data)

    # Mark the sheet
    report = await orchestrator.mark_answer_sheet(
        marking_guide=marking_guide,
        answer_sheet=answer_sheet,
        assessment_title="Financial Accounting"
    )

    # Save report
    report.to_json_file(Path("output/report.json"))

# Run
asyncio.run(mark_papers())
```

See `OLLAMA_TEST_RESULTS.md` and previous test scripts for complete examples.

#### Option 2: Upgrade Typer (When Available)

Monitor Typer releases for fixes to rich_utils integration:
- https://github.com/tiangolo/typer/issues

Once fixed upstream, update `pyproject.toml`:
```toml
typer = "^0.12.0"  # Or whatever version includes the fix
```

#### Option 3: Disable Rich Entirely

If you need the CLI urgently, you can completely remove Rich dependency (but you'll lose pretty formatting):

```bash
poetry remove rich
poetry add click  # Ensure Click is installed
```

Then remove all Rich imports and usage from `commands.py`.

### Technical Details

The issue occurs because:

1. Typer 0.9.x's `rich_utils._print_options_panel()` calls `param.make_metavar()` without `ctx`
2. Click 8.x's Parameter class requires `ctx` as first argument to `make_metavar()`
3. The monkey-patch fixes help rendering by temporarily wrapping `make_metavar()`
4. However, Click caches or checks parameter properties during argument parsing
5. The wrapped method interferes with Click's option value detection

### Attempted Fixes

1. ✅ Downgraded Typer from 0.12.0 to 0.9.4
2. ✅ Added `pretty_exceptions_enable=False`
3. ✅ Added `rich_markup_mode=None`
4. ❌ Environment variable `_TYPER_STANDARD_TRACEBACK=1`
5. ✅ Monkey-patch for help rendering
6. ❌ Monkey-patch restoration (causes side effects)

### Recommendation

**For development and production use: Use Python scripts directly (Option 1)**

The Python API works perfectly and gives you more control over the marking workflow. The CLI is a convenience wrapper, but the underlying system is fully functional via direct Python calls.

### Related Files

- `/src/answer_marker/cli/commands.py` - CLI implementation with monkey-patch
- `/docs/QUICK_SETUP_WITH_OLLAMA.md` - Includes Python script examples
- `/OLLAMA_TEST_RESULTS.md` - Test results using Python scripts
- `/SESSION_SUMMARY.md` - Overall session summary

Last Updated: November 6, 2025
