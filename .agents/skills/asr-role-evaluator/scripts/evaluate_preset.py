#!/usr/bin/env python3
"""Convenience CLI script for the asr-role-evaluator skill."""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Navigate 4 levels up: scripts -> asr-role-evaluator -> skills -> .agents -> REPO_ROOT
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../.."))

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.unified_benchmark import run_unified_benchmark

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Skill CLI: ASR & Role Matrix Evaluator")
    parser.add_argument("--script", type=str, default=None, help="Specific script ID (e.g. script1)")
    parser.add_argument("--goal", type=str, default=None, help="Specific goal key (e.g. official_hindi)")
    parser.add_argument("--asr", type=str, default=None, help="Specific ASR key (e.g. smart_bilingual)")
    parser.add_argument("--cross-all-asr", action="store_true", help="Cross-evaluate every ASR preset against every Role")
    parser.add_argument("--force-asr", action="store_true", help="Re-run ASR transcription")
    parser.add_argument("--dry-run", action="store_true", help="Run assertion engine in dry-run mode")
    args = parser.parse_args()

    s_list = [args.script] if args.script else None
    g_list = [args.goal] if args.goal else None
    a_list = [args.asr] if args.asr else None

    run_unified_benchmark(
        target_scripts=s_list,
        target_asrs=a_list,
        target_goals=g_list,
        cross_all_asr=args.cross_all_asr,
        force_asr=args.force_asr,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
