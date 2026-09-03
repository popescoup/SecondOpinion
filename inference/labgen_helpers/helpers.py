import json
import numpy as np
import os
import re
import datetime
from zoneinfo import ZoneInfo
import ast

SECURITY_PROMPT_FILE='../prompt_base/security_prompts.jsonl'

def windowsts_to_unixts(windows_ts):
    return datetime.datetime.strptime(windows_ts, "%m/%d/%Y %I:%M:%S %p").timestamp()

def unixts_to_windowsts(unix_ts):
    return datetime.datetime.fromtimestamp(float(unix_ts)).strftime("%m/%d/%Y %I:%M:%S %p")

def get_ts_from_auditd_line(line):
    l = line.split()
    for e in l:
        key_val = e.split("=")
        key = key_val[0]
        val = key_val[1]
        if key == "msg":
            found = re.search(r"audit\((.*?):(.*?)\):", val)
            if found:
                line_ts = float(found[1])
                return line_ts
            else:
                print("line with no timestamp: ", l)


def get_rawlog_timestamps(fpath, stidx, enidx):
    with open(fpath, 'r') as f:
        for i, line in enumerate(f):
            if i==stidx:
                st_timestamp = get_ts_from_auditd_line(line)
            if i==enidx:
                en_timestamp = get_ts_from_auditd_line(line)
    return st_timestamp, en_timestamp

def get_edgelog_timestamps(fpath, stidx, enidx):
    with open(fpath, 'r') as f:
        for i, line in enumerate(f):
            if i==stidx:
                found = re.search(r"\((.*?)\)", line)
                try:
                    st_timestamp = float(found.group(1))
                except ValueError:
                    st_timestamp = datetime.datetime.strptime(found.group(1), "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=ZoneInfo("US/Central")).timestamp()
            if i==enidx:
                found = re.search(r"\((.*?)\)", line)
                try:
                    en_timestamp = float(found.group(1))
                except ValueError:
                    en_timestamp = datetime.datetime.strptime(found.group(1), "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=ZoneInfo("US/Central")).timestamp()
    return st_timestamp, en_timestamp

def get_graphlog_timestamps(fpath, stidx, enidx):
    with open(fpath, 'r') as f:
        for i, line in enumerate(f):
            if i == stidx and line.startswith("**********"):
                stidx = stidx + 1
            if i == enidx and line.startswith("**********"):
                continue

            if i==stidx:
                found = re.search(r"\((.*?)\)", line)
                try:
                    st_timestamp = float(found.group(1))
                except ValueError:
                    st_timestamp = datetime.datetime.strptime(found.group(1), "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=ZoneInfo("US/Central")).timestamp()
            if i==enidx:
                found = re.search(r"\((.*?)\)", line)
                try:
                    en_timestamp = float(found.group(1))
                except ValueError:
                    en_timestamp = datetime.datetime.strptime(found.group(1), "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=ZoneInfo("US/Central")).timestamp()
    return st_timestamp, en_timestamp
                
def load_gpt_seclabel_reasoning_prompt(key):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.abspath(os.path.join(curr_dir, SECLABEL_REASONING_FILE))
    with open(full_path, 'r') as f:
        for line in f:
            d = json.loads(line, strict=False)
            for k in d:
                if k == key:
                    return d[k]

def read_security_consistency_resp(fname, llm):
    print(f"Consistency results of {llm}")
    consistency_dict = {}
    k = (None, None, None)
    with open(fname, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("****Starting line num: "):
                pattern = r"\*\*\*\*Starting line num: (\d+). Num lines: (\d+). (.*)\*\*\*\*"
                match = re.search(pattern, line)
                lnum = int(match.group(1))
                numlines = int(match.group(2))
                time = match.group(3)
                k = (lnum, numlines, time)
                if k not in consistency_dict:
                    consistency_dict[k] = []
            if line.startswith("Decision: "):
                pattern = r"Decision: ([a-zA-Z]+)"
                match = re.search(pattern, line)
                class_decision = match.group(1)
                class_decision = class_decision.lower()
                consistency_dict[k].append(class_decision)
    return consistency_dict

def get_timerange_from_llmoutput(consistency_dict):
    timerange = []
    start_times = []
    for k in consistency_dict:
        start_times.append(k[2])
    for i in range(len(start_times)-1):
        timerange.append((start_times[i], start_times[i+1]))
    return timerange

def read_outputs(fname, output_list, llm='gpt'):
    with open(fname, 'r') as f:
        outstr = ''
        for line in f:
            if line == f"-----------------------{llm}------------------------\n":
                # print(outstr)
                output_list.append(outstr)
                outstr = ''
            else:
                outstr += line
    return output_list

def write_correctness_labels(llm_outpath, gpt_output, gem_output, start_linenum, num_lines):
    with open(llm_outpath, 'a') as f:
        f.write(f"****Starting line no. {start_linenum}, num_lines {num_lines}****\n")
        f.write(f"GPT output: {gpt_output}\n")
        f.write(f"Gemini output: {gem_output}\n\n")

