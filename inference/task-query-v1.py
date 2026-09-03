from helpers import helpers
from labgen_helpers import helpers as labgenhelpers
from optc_helpers import helpers as optchelpers
from zoneinfo import ZoneInfo
from tqdm import tqdm
import os
import argparse
import datetime
import inference_helpers

# Maps the --llm value to the prompt-file family. The v1 prompts are stored, per task,
# in benchmark_{family}_prompts.jsonl (one file per task directory). Kimi reuses the
# Llama (Together) prompt file since it is served through the same client.
PROMPT_FAMILY = {
    "gpt": "gpt",
    "gemini": "gemini",
    "llama": "llama",
    "kimi": "llama",
}


def get_numrun_outputs(task, log_fpath, prompt_key, num_runs, stidx, enidx, temp, llm, model, dataset='labgen'):
    # Load a chunk of lines from the audit log
    data = helpers.load_logs(log_fpath, stidx, enidx)

    # The v1 prompt is a pre-built string stored in a per-task, per-model-family JSONL file.
    family = PROMPT_FAMILY.get(llm, llm)
    benchmark_prompt_file = f'../{dataset}_expt_dataset/task_{task}/benchmark_{family}_prompts.jsonl'

    # Load the desired prompt based on the prompt_key input variable, which should reflect the
    # correct version and representation type, then substitute in the log data.
    prompt = helpers.load_gemini_security_prompt(prompt_key, benchmark_prompt_file)
    message = prompt
    hardcoded_pattern = "{_input_data_}"
    if hardcoded_pattern in prompt:
        message = prompt.replace("_input_data_", str(data))

    # Run the LLM on this prompt num_runs times
    results = []
    for _ in tqdm(range(num_runs)):
        results.append(inference_helpers.call_model(llm, model, message, temp))

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run v1-prompt inference for any task on any supported LLM (GPT, Gemini, Llama/Kimi).")
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
    parser.add_argument("--batch_temp_file", type=str, required=False, default="./tmp/batch-temp-file.jsonl",
                        help="temporary file path containing batch requests")
    parser.add_argument("--model", type=str, required=False, default='gemini-2.5-flash',
                        help="model name to run the query, e.g. 'gpt-5-mini', 'gemini-2.5-flash', 'meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8'")
    parser.add_argument("--llm", type=str, required=False, default='gemini',
                        help="LLM for running experiment: 'gpt', 'gemini', 'llama', or 'kimi'")
    parser.add_argument("--task", type=str, required=True, help="task name: 'classification', 'lm', 'persistence', 'exfiltration'")

    args = parser.parse_args()

    assert args.dataset in args.log_fpath, "Mismatch in --dataset and --log_fpath flag"

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
    assert rep == "edge" or "raw" or "graph"

    # Create a name for the output file
    curr_date = datetime.datetime.now(ZoneInfo("US/Central")).date().strftime("%Y-%m-%d")

    prompt_key = args.prompt_key

    batch_output_file = helpers.create_output_filename(prompt_key, args.log_fpath, curr_date, args.temp, args.num_runs, args.model)

    outpath = f"./{args.dataset}_expt_dataset/task_{args.task}/{rep}/output/{args.llm}out/"+batch_output_file

    # Loop through the audit log in chunks
    # st_lno and en_lno are where we want to process the logs overall
    for i in range(st_lno, en_lno + (1 if st_lno == en_lno else 0), num_lines):
        stidx = i-1
        enidx = min(i + num_lines - 1, en_lno - 1)

        results = get_numrun_outputs(args.task, args.log_fpath, args.prompt_key, args.num_runs, stidx, enidx, args.temp, args.llm, args.model, args.dataset)

        # For each chunk of the audit log lines, get the LLM output, and get the time stamps corresponding
        # to when those audit logs were captured originally, for labeling
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
