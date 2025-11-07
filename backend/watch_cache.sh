#!/bin/bash

echo "=================================================="
echo "  Cache Hit Monitor - Watching Backend Logs"
echo "=================================================="
echo ""
echo "Watching for:"
echo "  ⚡ CACHE HIT     - File was cached (0 API calls)"
echo "  Processing NEW  - First time processing (uses API calls)"
echo ""
echo "Press Ctrl+C to stop"
echo "=================================================="
echo ""

tail -f backend_live.log | grep --line-buffered -E "(CACHE HIT|⚡|Processing NEW|Marking NEW|Saved uploaded|Successfully)"
