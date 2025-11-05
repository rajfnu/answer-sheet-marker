#!/usr/bin/env python
"""Direct CLI test"""

import sys
sys.path.insert(0, "src")

from answer_marker.cli.commands import app

if __name__ == "__main__":
    app()
