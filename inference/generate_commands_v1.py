
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
    num_lines = 1000 if rep == "raw" else 400


    # Set version keyword based on task
    if task == "lm":
        version = "v14"
    elif task == "persistence":
        version = "v9"
    elif task == "exfiltration":
        version = "v15"
    elif task == "classification":
        version = "v7"

    # Set temp based on model
    if model in {"gpt-5", "gpt-5-mini"}:
        temp = 1
    elif model in {"gemini-2.5-flash", "gemini-2.5-pro", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"}:
        temp = 0
    else:
        temp = 0  # Default to 0 if not specified

    #pull up the {scenario: os} mapping from benchmark_scenarios
    if dataset == "labgen":
        scenario_os_key = f"{dataset}_{task}_os"
        scenario_os_dict = getattr(benchmark_scenarios, scenario_os_key)

    for log_fname in scenario_list:
        if dataset == "labgen":
            os_type = scenario_os_dict[log_fname]
        elif dataset == "optc":
            os_type = "windows"
        else:
            raise NotImplementedError("Undefined dataset. Cannot find OS type.")

        prompt_key = f"{task}-investigation_{version}{os_type}_{task}_{dataset}_{rep}"
        print(f'python task-query-v1.py --dataset "{dataset}" --log_fpath "./{dataset}_expt_dataset/task_{task}/{rep}/input/{log_fname}" --num_lines {num_lines} --prompt_key "{prompt_key}" --num_runs 1 --temp {temp} --llm "{llm}" --model "{model}" --task "{task}"')
        print()


if __name__ == "__main__":
    main()
