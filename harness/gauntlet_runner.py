#!/usr/bin/env python3
"""Compatibility entry point for B1/B2 evaluation.

All authoritative runs delegate to harness.confirmation_runner so baseline cells
cannot diverge from S1/S2 in task loading, adapter rendering, generation policy,
or receipt creation.
"""

from __future__ import annotations

import argparse

from contract.schema import ExperimentCell, Partition
from harness.confirmation_runner import run_cell


def main() -> None:
    parser = argparse.ArgumentParser(description="Cognitive Core B1/B2 gauntlet runner")
    parser.add_argument("--both", action="store_true")
    parser.add_argument("--model", default="B1", choices=["B1", "B2", "b1", "b2"])
    parser.add_argument("--gauntlet", default=None)
    parser.add_argument("--partition", default="dev", choices=["dev", "replication", "lockbox"])
    parser.add_argument("--task-file", default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    cells = [ExperimentCell.B1, ExperimentCell.B2] if args.both else [ExperimentCell(args.model.upper())]
    partition = Partition(args.partition)

    summaries = []
    for cell in cells:
        summaries.append(
            run_cell(
                cell=cell,
                partition=partition,
                task_file=args.task_file,
                gauntlet_filter=args.gauntlet,
                seed=args.seed,
                verbose=not args.quiet,
            )
        )

    if len(summaries) == 2:
        b1, b2 = summaries
        print("\nB1 vs B2")
        print(f"  B1 pass rate: {b1['pass_rate']:.1%}")
        print(f"  B2 pass rate: {b2['pass_rate']:.1%}")
        print(f"  delta B2-B1:  {b2['pass_rate'] - b1['pass_rate']:+.1%}")


if __name__ == "__main__":
    main()
