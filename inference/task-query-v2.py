from helpers import helpers
from labgen_helpers import helpers as labgenhelpers
from optc_helpers import helpers as optchelpers
from zoneinfo import ZoneInfo
import os
import argparse
import datetime
import inference_helpers
import benchmark_scenarios

from prompt_v2 import Prompt
from prompt_template.input_format import InputFormat
from prompt_template.ostype import OSType
from prompt_template.lateralmovement_template_v2 import LateralMovementPrompt
from prompt_template.persistence_template_v2 import PersistencePrompt
from prompt_template.exfiltration_template_v2 import ExfiltrationPrompt
from prompt_template.classification_template_v2 import ClassificationPrompt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run v2-prompt inference for any task on any supported LLM (GPT, Gemini, Llama/Kimi).")
    parser.add_argument("--dataset", type=str, required=True, default="labgen", help="name of the dataset. 'labgen', 'optc'")
    parser.add_argument("--log_fpath", type=str, required=True, default="./dataset/sorted_provenance_08202024.jsonl",
                        help="path of log file")
    parser.add_argument("--num_lines", type=int, required=True, default=1000,
                        help='number of lines')
    parser.add_argument('--prompt_key', type=str, required=True, default='security v2',
                        help='enter the dictionary key from benchmark_prompts.jsonl file')
    parser.add_argument('--num_runs', type=int, default=10, required=True,
                        help='number of times to run the consistency experiment')
    parser.add_argument('--temp', type=float, default=1, required=True,
                        help='values between 0-2. lower values result in more consistent outputs (e.g. 0.2), while higher values generate more diverse and creative results(e.g. 1.0)')
    parser.add_argument("--start_lno", type=int, required=False, default=0,
                        help="if the input log file is too big, then specify start and end line numbers")
    parser.add_argument("--end_lno", type=int, required=False, default=0,
                        help="if the input log file is too big, then specify start and end line numbers")
    parser.add_argument("--model", type=str, required=False, default='gemini-2.5-flash',
                        help="model name to run the query, e.g. 'gpt-5-mini', 'gemini-2.5-flash', 'moonshotai/kimi-k2.5'")
    parser.add_argument("--llm", type=str, required=False, default='gemini',
                        help="LLM for running experiment: 'gpt', 'gemini', 'llama', or 'kimi'")
    parser.add_argument("--task", type=str, required=True, help="task name: 'classification', 'lm', 'persistence', 'exfiltration'")
    parser.add_argument("--custom_prompt", type=str, required=False, default=None,
                        help="Pass a custom prompt string or a path to a .txt file to override the default goal section of the prompt for the selected task.")

    args = parser.parse_args()

    assert args.dataset in args.log_fpath, "Mismatch in --dataset and --log_fpath flag"

    assert args.task in {'lm', 'persistence', 'exfiltration', 'classification'}, "Undefined task"

    custom_goal_text = None
    if args.custom_prompt:
        if os.path.isfile(args.custom_prompt):
            with open(args.custom_prompt, 'r') as f:
                custom_goal_text = f.read().strip()
        else:
            custom_goal_text = args.custom_prompt

    if args.start_lno and args.end_lno:
        st_lno = args.start_lno
        en_lno = args.end_lno
    elif args.start_lno != 0 and args.end_lno == 0:
        st_lno = args.start_lno
        en_lno = inference_helpers.count_total_lines(args.log_fpath)
    elif args.start_lno == 0 and args.end_lno != 0:
        st_lno = 1
        en_lno = args.end_lno
    else:
        st_lno = 1
        en_lno = inference_helpers.count_total_lines(args.log_fpath)

    num_lines = args.num_lines
    rep = args.log_fpath.split("/")[-1].split("_")[0]

    curr_date = datetime.datetime.now(ZoneInfo("US/Central")).date().strftime("%Y-%m-%d")
    prompt_key = args.prompt_key

    output_file = helpers.create_output_filename(prompt_key, args.log_fpath, curr_date, args.temp, args.num_runs, args.model)
    outpath = f"./{args.dataset}_expt_dataset/task_{args.task}/{rep}/output/{args.llm}out/"+output_file

    scenario = args.log_fpath.split("/")[-1]
    if args.dataset == "labgen":
        os_type = getattr(benchmark_scenarios, f"{args.dataset}_{args.task}_os")[scenario]
    else:
        os_type = "windows"

    if args.task == "lm":
        task_prompt = Prompt(
            task = "lateral movement",
            os_type = getattr(OSType, os_type),
            goal = custom_goal_text if custom_goal_text else LateralMovementPrompt.GOAL,
            output_description = LateralMovementPrompt.OUTPUT_DESCRIPTION,
            json_output_format = LateralMovementPrompt.OUTPUT_FORMAT,
            log_input_format = getattr(InputFormat, rep)
        )

    if args.task == "persistence":
        task_prompt = Prompt(
            task = "persistence",
            os_type = getattr(OSType, os_type),
            goal = custom_goal_text if custom_goal_text else PersistencePrompt.GOAL,
            output_description = PersistencePrompt.OUTPUT_DESCRIPTION,
            json_output_format = PersistencePrompt.OUTPUT_FORMAT,
            log_input_format = getattr(InputFormat, rep),
            additional_sections=PersistencePrompt.ADDITIONAL_SECTION,
            mitre_output=PersistencePrompt.OUTPUT_FORMAT_MITRE,
        )

    if args.task == "exfiltration":
        task_prompt = Prompt(
            task = "exfiltration",
            os_type = getattr(OSType, os_type),
            output_description = ExfiltrationPrompt.OUTPUT_DESCRIPTION,
            goal = custom_goal_text if custom_goal_text else ExfiltrationPrompt.GOAL,
            json_output_format = ExfiltrationPrompt.OUTPUT_FORMAT,
            log_input_format = getattr(InputFormat, rep),
        )

    if args.task == "classification":
        task_prompt = Prompt(
        task = "attack",
        os_type = getattr(OSType, os_type),
        output_description = ClassificationPrompt.OUTPUT_DESCRIPTION,
        goal = custom_goal_text if custom_goal_text else ClassificationPrompt.GOAL,
        json_output_format = ClassificationPrompt.OUTPUT_FORMAT,
        log_input_format = getattr(InputFormat, rep),
    )

    fpath = f"./{args.dataset}_expt_dataset/task_{args.task}/benchmark_{args.llm}_prompts.jsonl"
    task_prompt.save_prompt(fpath, args.prompt_key, task_prompt.populate("_input_data_"))

    for i in range(st_lno, en_lno + (1 if st_lno == en_lno else 0), num_lines):
        stidx = i-1
        enidx = min(i + num_lines - 1, en_lno - 1)

        results = inference_helpers.get_numrun_outputs(args.log_fpath, task_prompt, args.num_runs, stidx, enidx, args.temp, args.llm, args.model, args.dataset)

        if args.dataset == "labgen":
            if rep == "raw":
                log_start_ts, log_end_ts = labgenhelpers.get_rawlog_timestamps(args.log_fpath, stidx, enidx)
            elif rep == "edge":
                log_start_ts, log_end_ts = labgenhelpers.get_edgelog_timestamps(args.log_fpath, stidx, enidx)
            elif rep == "graph":
                log_start_ts, log_end_ts = labgenhelpers.get_graphlog_timestamps(args.log_fpath, stidx, enidx)
        elif args.dataset == "optc":
            if rep == "raw":
                pass #TODO: implement this later if needed
            elif rep == "edge":
                log_start_ts, log_end_ts = optchelpers.get_edgelog_timestamps(args.log_fpath, stidx, enidx)

        if log_start_ts != None:
            log_start_ts = helpers.unixts_to_string(log_start_ts)
        if log_end_ts != None:
            log_end_ts = helpers.unixts_to_string(log_end_ts)

        inference_helpers.write_completionapi_results(results, outpath, stidx+1, num_lines, args.llm, f"{log_start_ts}-to-{log_end_ts}")
