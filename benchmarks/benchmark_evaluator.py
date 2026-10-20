#!/usr/bin/env python3
"""Backward-compatible wrapper redirecting to Unified Benchmark."""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from unified_benchmark import run_unified_benchmark

def run_benchmark(dry_run: bool = False, target_script: str = None):
    s_list = [target_script] if target_script else None
    return run_unified_benchmark(target_scripts=s_list, dry_run=dry_run)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_benchmark(target_script=target)
