"""Count tokens in every 400-line chunk of the edge scenario logs.

Run from the repo's top-level folder:
    python scripts/check_chunk_tokens.py

Flags any chunk that would not fit gpt-oss-120b's context window once the
prompt template and the harness's 16,384-token output budget are reserved.
"""
import glob
import os
import sys

import tiktoken

CHUNK_LINES = 400                 # the paper's chunk size for the edge representation
CONTEXT = 131_072                 # gpt-oss-120b context window
OUTPUT_BUDGET = 16_384            # max_tokens used by the harness
PROMPT_OVERHEAD = 3_000           # rough size of the v2 prompt template around the logs
LIMIT = CONTEXT - OUTPUT_BUDGET - PROMPT_OVERHEAD

enc = tiktoken.get_encoding("o200k_base")  # gpt-oss uses this tokenizer family

pattern = "inference/*_expt_dataset/task_*/edge/input/*.log"
files = sorted(glob.glob(pattern))
if not files:
    sys.exit(f"No files matched {pattern}. Run this from the repo's top-level folder.")

counts, too_big = [], []
for path in files:
    with open(path, errors="ignore") as f:
        lines = f.read().splitlines(keepends=True)
    for start in range(0, len(lines), CHUNK_LINES):
        n = len(enc.encode("".join(lines[start:start + CHUNK_LINES])))
        counts.append(n)
        if n > LIMIT:
            parts = path.split(os.sep)
            dataset = parts[1].split("_")[0]       # labgen or optc
            task = parts[2].removeprefix("task_")
            too_big.append((n, dataset, task, os.path.basename(path), start + 1))

counts.sort()
print(f"Files: {len(files)}   Chunks: {len(counts)}")
print(f"Tokens per chunk: median {counts[len(counts) // 2]:,}   "
      f"90th pct {counts[int(len(counts) * 0.9)]:,}   max {counts[-1]:,}")
print(f"Total log tokens across all chunks: {sum(counts):,}")
print(f"Input budget for gpt-oss at {CHUNK_LINES} lines: {LIMIT:,} tokens")
print(f"Chunks over budget: {len(too_big)}")
for n, dataset, task, name, line in sorted(too_big, reverse=True):
    print(f"  {n:>8,}  {dataset:6s} {task:15s} {name}  (chunk starting line {line})")
