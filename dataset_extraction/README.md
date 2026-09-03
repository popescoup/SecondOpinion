# Dataset Extraction — Post-Processing of SPADE Logs

This directory contains the complete pipeline for turning the `.log` files collected
from Windows and Linux machines into the per-scenario **raw** and **edge**
representations used as LLM input.

Run everything from inside this directory with the project conda env active:

```bash
conda activate llmeval
cd dataset_extraction
```

---

## Script inventory

| Script | Stage | OS | Purpose |
|--------|-------|----|---------|
| `remove_rawlogs_key.py`          | raw  | Linux        | Strip `key=...` tokens from auditd lines (prevents the LLM cheating off auditd rule keys) |
| `remove_rawlogs_scan.py`         | raw  | Linux        | Drop SSH scan lines (`terminal=ssh res=failed'` / `terminal=sshd res=failed'`) |
| `extract_rawlog_lines.py`        | raw  | Linux        | Slice the cleaned raw log to a scenario's `[start, end)` timestamp window |
| `sort_json.py`                   | edge | Linux/Win    | Sort SPADE JSON output by edge timestamp → JSONL (also reorders node metadata) |
| `convert_labgen_linux_edge.py`   | edge | Linux        | Sorted JSONL → edge representation (`.log`) |
| `convert_labgen_windows_edge.py` | edge | Windows      | Sorted JSONL → edge representation (`.log`) |
| `extract_linuxedge_lines.py`     | edge | Linux        | Slice edge rep to scenario window **+ dedup** (US/Central tz) |
| `extract_windowsedge_lines.py`   | edge | Windows      | Slice edge rep to scenario window **+ dedup** |
| `deduplicate_edges.py`           | edge | Linux/Win    | Dedup helper imported by both `extract_*edge_lines.py`; also runnable standalone |

> `extract_linuxedge_lines.py` and `extract_windowsedge_lines.py` `import deduplicate_edges`,
> so keep `deduplicate_edges.py` in the same directory as those two scripts.

Dependencies (already in the `llmeval` env): `tqdm`, `pytz`, plus the Python stdlib.

---

## Collecting logs with SPADE (Linux, upstream of this directory)

Reference: https://github.com/ashish-gehani/SPADE/wiki/Starting-and-controlling-SPADE

On the collection VM:

```bash
cd SPADE/bin
./spade start
./spade control
```

Inside the SPADE control interface:

```
list all                       # see current configuration
remove reporter JSON           # remove the JSON reporter if already present
add storage JSON output=~/spade_output/provenance_20240909_20250531.json
add reporter Audit fileIO=true netIO=true localEndpoints=true namespaces=true IPC=true networkAddressTranslation=true inputLog=/var/log/audit/audit.log
```

Then move the SPADE JSON output to the `spade_output/` working directory (used in Pipeline B).

---

## Pipeline A — Raw representation (Linux `audit.log`)

Order matters: remove keys → remove scans → extract scenario window.

**1. Remove keys**
```bash
python remove_rawlogs_key.py \
  --input_fpath "./data/audit_20240909-20250531.log" \
  --out_fpath   "./data/audit_20240909-20250531_keyremoved.log" \
  --system_os linux
```

**2. Remove scans**
```bash
python remove_rawlogs_scan.py \
  --input_fpath "./data/audit_20240909-20250531_keyremoved.log" \
  --out_fpath   "./data/audit_20240909-20250531_scanremoved.log"
```
(Or `--task <task> --all_files 1` to clean every `.log` under
`../scenarios/<task>/raw` in place.)

**3. Extract a scenario by timestamp window**
```bash
python extract_rawlog_lines.py \
  --start_time "2025-05-31 18:17" \
  --end_time   "2025-05-31 18:23" \
  --input_fpath "./data/audit_20240909-20250531_scanremoved.log" \
  --out_fpath   "../scenarios/classification/raw/raw_2025-05-31T18-17-to-2025-05-31T18-23_benign-scenario7.log"
```

---

## Pipeline B — Edge representation

### B1. Sort the SPADE JSON → JSONL (Linux or Windows)

Copy the SPADE JSON output into `spade_output/`; the sorted JSONL is written
alongside it.

```bash
# Linux
python sort_json.py \
  --input_fpath "../spade_output/linux/provenance_20240909_20250531.json" \
  --out_fpath   "../spade_output/linux/sorted_provenance_20240909_20250531.jsonl" \
  --system_os linux

# Windows
python sort_json.py \
  --input_fpath "../spade_output/lateral_movement/lm_tech_1_20250113.json" \
  --out_fpath   "../spade_output/lateral_movement/sorted_lm_tech_1_20250113.jsonl" \
  --system_os windows
```

### B2. Convert sorted JSONL → edge representation

```bash
# Linux
python convert_labgen_linux_edge.py \
  --input_fpath "../spade_output/linux/sorted_provenance_20240909_20250531.jsonl" \
  --out_fpath   "../spade_output/linux/linux_edgerep_20240909_20250531.log"

# Windows
python convert_labgen_windows_edge.py \
  --input_fpath "../spade_output/lateral_movement/sorted_lm_tech_1_20250113.jsonl" \
  --out_fpath   "../spade_output/lateral_movement/edge/edge_lm_tech_1_20250113.log"
```

Edge line format (type is added as a node attribute; each edge gets a unique edge id):
```
(timestamp) [SrcID]{src attrs} --> [EdgeID]{edge attrs} --> [DstID]{dst attrs}
```

### B3. Extract a scenario window from the edge representation (dedup built in)

There are separate extractors for Linux and Windows. **Both run de-duplication
internally**, so there is no need to run `deduplicate_edges.py` separately.

```bash
# Linux  (timestamps interpreted in US/Central)
python extract_linuxedge_lines.py \
  --start_time "2025-05-31 17:49" \
  --end_time   "2025-05-31 17:54" \
  --input_fpath "../spade_output/linux/linux_edgerep_20240909_20250531.log" \
  --out_fpath   "../scenarios/exfiltration/edge/edge_2025-05-31T17-49-to-2025-05-31T17-54_exfiltration-scenario4.log" \
  --system_os linux

# Windows
python extract_windowsedge_lines.py \
  --input_fpath "../spade_output/attack_combination/edge/edge_attack-combination-1_deduplicated.log" \
  --out_fpath   "../spade_output/attack_combination/edge/trimmed_edge_attack-combination-1_deduplicated.log" \
  --system_os windows \
  --start_ts "2025-01-02 22:28" \
  --end_ts   "2025-01-02 22:34"
```

### (Optional) Standalone de-duplication
```bash
python deduplicate_edges.py \
  --input_fpath "<edge.log>" --out_fpath "<edge_deduplicated.log>" --system_os linux   # or windows
```
