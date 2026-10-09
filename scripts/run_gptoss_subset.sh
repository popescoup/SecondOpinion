#!/usr/bin/env bash
# Parity baseline: gpt-oss-120b through the UNMODIFIED harness (Together API),
# on the fixed 8-scenario lab edge subset (44 chunks), 2 runs per chunk.
#
# Run from the repo's top-level folder:
#   caffeinate -i bash scripts/run_gptoss_subset.sh 2>&1 | tee gptoss_together_baseline.log

set -euo pipefail
cd "$(dirname "$0")/../inference"
export TZ=America/Chicago   # the scorer and ground truth assume US Central time

MODEL="openai/gpt-oss-120b"
SUBSET=(
  "classification attack-linux-scenario2"
  "classification benign-scenario3"
  "exfiltration exfiltration-scenario1"
  "exfiltration benign-scenario3"
  "lm lm-scenario2"
  "lm benign-scenario3"
  "persistence persistence-scenario1"
  "persistence benign-scenario3"
)

for spec in "${SUBSET[@]}"; do
  read -r task scen <<< "$spec"
  f=$(ls labgen_expt_dataset/task_${task}/edge/input/*_${scen}.log)
  echo "=== $(date '+%H:%M:%S')  $task / $scen ==="
  python task-query-v2.py --dataset labgen --task "$task" --log_fpath "./$f" \
    --num_lines 400 --prompt_key "${task}-investigation_v2_${task}_labgen_edge" \
    --num_runs 2 --temp 0 --llm llama --model "$MODEL"
done
echo "=== $(date '+%H:%M:%S')  done ==="
