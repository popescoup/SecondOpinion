
import importlib
import sys
import argparse

# Dynamically import the benchmark_scenarios module
benchmark_scenarios = importlib.import_module("benchmark_scenarios")

def main():
    parser = argparse.ArgumentParser(description="Generate python commands for LLM evaluation.")
    parser.add_argument('--dataset', required=True, help='Dataset name')
    parser.add_argument('--task', required=True, help='Task name')
    parser.add_argument('--rep', required=True, choices=['raw', 'edge'], help='Representation (raw/edge)')
    parser.add_argument('--type', required=True, help='Type (benign/attack)')
    parser.add_argument('--llm', required=True, help='LLM name')
    parser.add_argument('--model', required=True, help='Model name')
    parser.add_argument('--num_lines', required=False, default=None, help='Number of lines of logs for running inferences.')
    args = parser.parse_args()

    dataset = args.dataset
    task = args.task
    rep = args.rep
    typ = args.type
    llm = args.llm
    model = args.model

    assert args.llm in {"gpt", "gemini", "llama", "kimi"}, "undefined --llm value"

    allowed_tasks = {"lm", "persistence", "exfiltration", "classification"}
    if task not in allowed_tasks:
        print(f"Error: task must be one of {allowed_tasks}. Got '{task}' instead.")
        sys.exit(1)

    if llm == "gemini":
        assert "gemini" in model, "Incompatable LLM and model"
    if llm == "gpt":
        assert "gpt" in model, "Incompatable LLM and model"
    if llm == "llama":
        assert "llama" in model.lower(), "Incompatable LLM and model"
    if llm == "kimi":
        assert "kimi" in model.lower(), "Incompatable LLM and model"

    # Construct the variable name
    var_name = f"{dataset}_{task}_{rep}_{typ}"

    # Try to get the list from benchmark_scenarios
    try:
        scenario_list = getattr(benchmark_scenarios, var_name)
    except AttributeError:
        print(f"No such scenario list: {var_name}")
        sys.exit(1)

    # Set num_lines based on rep
    if args.num_lines is None:
        num_lines = 1000 if rep == "raw" else 400
    else:
        num_lines = args.num_lines

    # Prompt version label. Every task uses the single v2 prompt template (prompt_v2.py). The label
    # is embedded in --prompt_key and therefore in the output file name, which the v2 parsers and
    # metrics scripts rely on to recognise v2 outputs.
    version = "v2"

    prompt_key = f"{task}-investigation_{version}_{task}_{dataset}_{rep}"

    # Set temp based on model
    if model in {"gpt-5", "gpt-5-mini"}:
        temp = 1
    elif model in {"gemini-2.5-flash", "gemini-2.5-pro", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"}:
        temp = 0
    else:
        temp = 0  # Default to 0 if not specified

    for log_fname in scenario_list:
        # All models and tasks share the single v2 inference script; --llm/--model select the model.
        print(f'python task-query-v2.py --dataset "{dataset}" --log_fpath "./{dataset}_expt_dataset/task_{task}/{rep}/input/{log_fname}" --num_lines {num_lines} --prompt_key "{prompt_key}" --num_runs 1 --temp {temp} --llm "{llm}" --model "{model}" --task "{task}"')
        print()


if __name__ == "__main__":
    main()