import json
import itertools
import datetime
import re
import benchmark_scenarios
import os
import ast

def get_fname(dirpath, scenario_name, model):
    for e in os.listdir(dirpath):
        if os.path.isfile(os.path.join(dirpath, e)) and scenario_name in e and model in e:
            outpath = os.path.join(dirpath, e)
            return outpath

# ---------------------------------------------------------------------------------------------
# Prompt versions.
#
# This repository has exactly TWO prompt versions:
#   * "v1" - the legacy, hand-written prompts stored in benchmark_<llm>_prompts.jsonl
#   * "v2" - the current templated prompt (prompt_v2.py + prompt_template/*_template_v2.py)
#
# Both labels were renamed: the v2 prompt used to be labelled "v3" and the v1 prompt used to be
# labelled "v0". There is NO other prompt version: wherever a stray "v3" or "v0" still shows up
# (e.g. in the name of an LLM output file generated before the rename, or in the --version flag
# of an old shell script), "v3" means prompt v2 and "v0" means prompt v1. The helpers below
# implement that aliasing in one place so that older artefacts and commands keep working.
# ---------------------------------------------------------------------------------------------
PROMPT_VERSIONS = ("v1", "v2")
LEGACY_PROMPT_VERSION_ALIASES = {"v3": "v2", "v0": "v1"}


def normalize_prompt_version(version: str) -> str:
    """Map a legacy prompt-version label to the current one ("v3" -> "v2", "v0" -> "v1"); others pass through."""
    return LEGACY_PROMPT_VERSION_ALIASES.get(version, version)


def has_prompt_version_label(fname: str, version: str) -> bool:
    """Return True if the LLM output file `fname` was generated with prompt `version`.

    Output files are named "{prompt_type}_{prompt_version}_{model}_{log_fname}_...", so the
    version label is matched as "_{label}_". Legacy labels that alias to `version` are accepted
    too (e.g. "_v3_" files are v2 outputs).
    """
    version = normalize_prompt_version(version)
    labels = {version} | {legacy for legacy, current in LEGACY_PROMPT_VERSION_ALIASES.items() if current == version}
    return any(f"_{label}_" in fname for label in labels)


class Parser:
    def __init__(self, dataset, task):
        self.dataset = dataset
        self.task = task
        self.ground_truth = f"./{dataset}_expt_dataset/task_{task}/groundtruth-{task}.jsonl"

    def process_timestamp(self, ts_line):
        gtfriendly_timestamp = None
        if ts_line:
            if ts_line[-1] == ",":
                ts_line = ts_line[:-1]

            ts_str = "{" + ts_line + "}"
            try:
                ts_dict = ast.literal_eval(ts_str)
                key = list(ts_dict.keys())[0]
                val = list(ts_dict.values())[0]

                assert key == "timestamp", "key is not equal to 'timestamp'"
                
                gtfriendly_timestamp = self.convert_ts_to_groundtruth_friendly(val)
            except:
                gtfriendly_timestamp = "Coundn't parser timestamp"
        return gtfriendly_timestamp
    
    def process_pid(self, pid_line):
        pid = None
        if pid_line:
            if pid_line[-1] == ",":
                pid_line = pid_line[:-1]
            
            pid_line = pid_line.split(":")
            key = pid_line[0].strip().strip('"')
            val = pid_line[1].strip().strip('"')
            assert key == "pid", "key is not equal to 'pid'"
            pid = val
        return pid
    
    def process_evidencefor(self, evidencefor_line):
        evidencefor = None
        if evidencefor_line:
            if evidencefor_line[-1] == ",":
                evidencefor_line = evidencefor_line[:-1]
            evidencefor_line = evidencefor_line.split(":", 1)
            key = evidencefor_line[0].strip().strip('"')
            val = evidencefor_line[1].strip().strip('"')
            assert key == "evidence for", "key is not equal to 'evidence for'"
            evidencefor = val
        return evidencefor
    
    def process_evidenceagainst(self, evidenceagainst_line):
        evidenceagainst = None
        if evidenceagainst_line:
            if evidenceagainst_line[-1] == ",":
                evidenceagainst_line = evidenceagainst_line[:-1]
            evidenceagainst_line = evidenceagainst_line.split(":", 1)
            key = evidenceagainst_line[0].strip().strip('"')
            val = evidenceagainst_line[1].strip().strip('"')
            assert key == "evidence against", "key is not equal to 'evidence against'"
            evidenceagainst = val
        return evidenceagainst

    def process_deliberation(self, deliberation_line):
        deliberation = None
        if deliberation_line:
            if deliberation_line[-1] == ",":
                deliberation_line = deliberation_line[:-1]
            deliberation_line = deliberation_line.split(":", 1)
            key = deliberation_line[0].strip().strip('"')
            val = deliberation_line[1].strip().strip('"')
            assert key == "deliberation", "key is not equal to 'deliberation'"
            deliberation = val
        return deliberation

    def process_conclusion(self, conclusion_line):
        conclusion = None
        if conclusion_line:
            if conclusion_line[-1] == ",":
                conclusion_line = conclusion_line[:-1]
            conclusion_line = conclusion_line.split(":", 1)
            key = conclusion_line[0].strip().strip('"')
            val = conclusion_line[1].strip().strip('"')
            assert key == "conclusion", "key is not equal to 'conclusion'"
            conclusion = val
        return conclusion

    def process_verdict(self, verdict_line):
        verdict = None
        if verdict_line:
            if verdict_line[-1] == ",":
                verdict_line = verdict_line[:-1]
            verdict_line = verdict_line.split(":")
            key = verdict_line[0].strip().strip('"')
            val = verdict_line[1].strip().strip('"')
            assert key == "verdict", "key is not equal to 'verdict'"
            verdict = val
        return verdict
    
    #for parsing the outputs of older prompt version
    def process_explanation(self, explanation_line):
        explanation = None
        if explanation_line:
            if explanation_line[-1] == ",":
                explanation_line = explanation_line[:-1]
            explanation_line = explanation_line.split(":", 1)
            key = explanation_line[0].strip().strip('"')
            val = explanation_line[1].strip().strip('"')
            assert key == "evidence" or "explanation", "key is not equal to 'evidence' or 'explanation'"
            explanation = val
        return explanation
    
    #for parsing the output of the legacy v1 prompt version
    def process_mitretechnique(self, mitre_technique_line):
        mitre_technique = None
        if mitre_technique_line:
            if mitre_technique_line[-1] == ",":
                mitre_technique_line = mitre_technique_line[:-1]
            mitre_technique_line = mitre_technique_line.split(":", 1)
            key = mitre_technique_line[0].strip().strip('"')
            val = mitre_technique_line[1].strip().strip('"')
            assert key == "MITRE technique", "key is not equal to 'MITRE technique'"
            mitre_technique = val
        return mitre_technique
    
    def convert_ts_to_groundtruth_friendly(self, timestamp):
        if self.dataset == "labgen":
            try:
                """labgenerated Windows logs are in format '%m/%d/%Y %I:%M:%S %p' """
                dt = datetime.datetime.strptime(timestamp, '%m/%d/%Y %I:%M:%S %p')
                if self.task == "lm":
                    """upto second precision for lateral movement task"""
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    """upto minute precision for persistence and exfiltration tasks"""
                    return dt.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                """`timestamp` is not string"""
                pass

            m = re.search(r"\d+\.\d+", timestamp)
            """labgenerated Linux logs have timestamps in the float format Unix timestmap """
            if m:
                try:
                    ts = float(m.group(0))
                    if self.task == "lm":
                        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    """timestamp not in float format"""
                    pass
            
            return None

        if self.dataset == "optc":
            """
            In OpTC dataset for all tasks, we consider timestamps upto a second precision 
            for the computation of precision and recall
            """
            return timestamp
        return None

    def read_task_groudtruth(self, groundtruth_key=None):
        if groundtruth_key is None:
            raise ValueError("Error: groundtruth_key argument is requred to read ground truths")

        groundtruth_set = set()
        fpath = f"./{self.dataset}_expt_dataset/task_{self.task}/groundtruth-{self.task}.jsonl"

        with open(fpath, "r") as f:
            for line in f:
                d = json.loads(line)
                key = list(d.keys())[0]
                if key == groundtruth_key:
                    val = d[key]
                    for dict_elem in val:
                        if self.task == "lm":
                            timestamp = dict_elem["timestamp"]
                            external_host = dict_elem["external host"]
                            username = dict_elem["username"]
                            tmp_set = set(itertools.product(timestamp, external_host))
                            groundtruth_set.update(tmp_set)
                        
                        if self.task == "persistence":
                            timestamps = dict_elem["timestamp"]
                            label = dict_elem["mechanism_name"]
                            groundtruth_set = set(itertools.product(timestamps, label))
                        
                        if self.task == "exfiltration":
                            timestamp = dict_elem["timestamp"]
                            exfiltrated_data = dict_elem["exfiltrated data"]
                            for e in exfiltrated_data:
                                e = e.replace(r"\\\\", "\\")
                                e = e.replace(r"\\", "\\")
                            groundtruth_set = set(itertools.product(timestamp, exfiltrated_data))
        
        return groundtruth_set