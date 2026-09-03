import argparse
import os
import re
import sys

# Add the parent directory (inference/) and project root to sys.path so that modules can be imported
# This allows the script to be run from the inference/ directory
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)  # inference/
project_root = os.path.dirname(parent_dir)  # auditbench/
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from metrics_comp import metrics_comp_utils
import numpy as np
from metrics_comp.factory import ModuleFactory
import benchmark_scenarios
from parser.customparser import PROMPT_VERSIONS, LEGACY_PROMPT_VERSION_ALIASES, normalize_prompt_version, has_prompt_version_label

import logging
FUNCTIONPRINT_LEVEL = logging.INFO + 5
logging.addLevelName(FUNCTIONPRINT_LEVEL, "FUNCTIONPRINT")

def functionprint(self, message, *args, **kwargs):

    if self.isEnabledFor(FUNCTIONPRINT_LEVEL):
    
        self._log(FUNCTIONPRINT_LEVEL, message, args, **kwargs)
    

logging.Logger.functionprint = functionprint

from paper_metrics.aggregate_metrics import sum_tp_fp, count_aggregate_from_dict

def get_scenario_number(outpath_list):
    match = re.search(r'scenario(\d+)', outpath_list[1])
    if match:
        return int(match.group(1))
    return float('inf')


def get_classification_gtclass(groundtruth_key):
    if "attack" in groundtruth_key:
        return "malicious"
    else:
        return "benign"


def get_groundtruth_key(outpath_tup, dataset) -> str:
    if dataset == "labgen":
        groundtruth_key = outpath_tup[0].split("/")[-1].split("_")[5].split(".")[0]
    if dataset == "optc":
        groundtruth_key = outpath_tup[0].split("/")[-1].split("_")[6].split(".")[0]
    
    return groundtruth_key


def count_scenario_loglines(fpath):
    cnt = 0
    with open(fpath, 'r') as f:
        for _ in f:
            cnt += 1
    return cnt


def get_outpathlist_regular(LLMOUTPUT_DIR, model, task, additional_output_id, scenario_type):
    outpath_list = []
    for e in os.listdir(LLMOUTPUT_DIR):
        if task in {"lm", "persistence", "exfiltration"}:
            if "attack" in scenario_type:
                if os.path.isfile(os.path.join(LLMOUTPUT_DIR, e)) and f"_{model}_" in e and f"{task}-scenario" in e and has_prompt_version_label(e, additional_output_id):
                    outpath_list.append((os.path.join(LLMOUTPUT_DIR, e), e, LLMOUTPUT_DIR))
            if "benign" in scenario_type:
                if os.path.isfile(os.path.join(LLMOUTPUT_DIR, e)) and f"_{model}_" in e and f"{scenario_type}-scenario" in e and has_prompt_version_label(e, additional_output_id):
                    outpath_list.append((os.path.join(LLMOUTPUT_DIR, e), e, LLMOUTPUT_DIR))
        
        elif task in {"classification"}:
            if os.path.isfile(os.path.join(LLMOUTPUT_DIR, e)) and f"_{model}_" in e and scenario_type in e and has_prompt_version_label(e, additional_output_id):
                # and "velox" not in e:
                outpath_list.append((os.path.join(LLMOUTPUT_DIR, e), e, LLMOUTPUT_DIR))
    return outpath_list

def get_outpathlist_rawequivalent(LLMOUTPUT_DIR, dataset, model, task, additional_output_id, scenario_type):
    """
    This function is just relevant for Lab data scenarios
    """
    outpath_list = []
    
    raw_scenarios_list = getattr(benchmark_scenarios, f"{dataset}_{task}_raw_{scenario_type}")
    raw_scenarios_set_namesuffix = set()

    for e in raw_scenarios_list:
        scenario_suffix = e.split("_", 1)[1]
        raw_scenarios_set_namesuffix.add(scenario_suffix)

    for e in os.listdir(LLMOUTPUT_DIR):
        if task in {"lm", "persistence", "exfiltration"}:
            if "attack" in scenario_type:
                if os.path.isfile(os.path.join(LLMOUTPUT_DIR, e)) and f"_{model}_" in e and f"{task}-scenario" in e and has_prompt_version_label(e, additional_output_id):
                    for raw_eqfname in raw_scenarios_set_namesuffix:
                        if raw_eqfname in e:
                            outpath_list.append((os.path.join(LLMOUTPUT_DIR, e), e, LLMOUTPUT_DIR))
            if "benign" in scenario_type:
                if os.path.isfile(os.path.join(LLMOUTPUT_DIR, e)) and f"_{model}_" in e and f"{scenario_type}-scenario" in e and has_prompt_version_label(e, additional_output_id):
                    for raw_eqfname in raw_scenarios_set_namesuffix:
                        if raw_eqfname in e:
                            outpath_list.append((os.path.join(LLMOUTPUT_DIR, e), e, LLMOUTPUT_DIR))
        
        elif task in {"classification"}:
            if os.path.isfile(os.path.join(LLMOUTPUT_DIR, e)) and f"_{model}_" in e and scenario_type in e and has_prompt_version_label(e, additional_output_id):
                for raw_eqfname in raw_scenarios_set_namesuffix:
                    if raw_eqfname in e:
                        outpath_list.append((os.path.join(LLMOUTPUT_DIR, e), e, LLMOUTPUT_DIR))
    
    # print("Outpath list: ", outpath_list)
    return outpath_list


def computation_setup(version, dataset, rep, llm, llmoutput_fname, all_scenarios, model, scenario_type, task, quiet, allscenarios_type="regular"):
    
    if quiet:
        log_level = FUNCTIONPRINT_LEVEL
    
    else:
        log_level = logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(message)s',
        stream=sys.stdout
    )

    assert task in {"lm", "persistence", "exfiltration", "classification"}, "Not acceptable task"

    LLMOUTPUT_DIR=f"./{dataset}_expt_dataset/task_{task}/{rep}/output/{llm}out"

    outpath_list = []
    if all_scenarios:

        assert scenario_type in {"benign", "attack"}, "scenario_type must be either 'benign' or 'attack'"

        # if task == "lm":
        #     if version == "v1":
        #         additional_output_id = "v14"
        #     elif version == "v2":
        #         additional_output_id = "v18"
        # if task == "persistence":
        #     if version == "v1":
        #         additional_output_id = "v9"
        #     elif version == "v2":
        #         additional_output_id = "v14"
        # if task == "exfiltration":
        #     if version == "v1":
        #         additional_output_id = "v15"
        #     elif version == "v2":
        #         additional_output_id = "v18"
        # if task == "classification":
        #     if version == "v1":
        #         additional_output_id = "v7"
        #     elif version == "v2":
        #         additional_output_id = "v11"
        if task == "lm":
            if version == "v1":
                additional_output_id = "v1"
            elif version == "v2":
                additional_output_id = "v2"
        if task == "persistence":
            if version == "v1":
                additional_output_id = "v1"
            elif version == "v2":
                additional_output_id = "v2"
        if task == "exfiltration":
            if version == "v1":
                additional_output_id = "v1"
            elif version == "v2":
                additional_output_id = "v2"
        if task == "classification":
            if version == "v1":
                additional_output_id = "v1"
            elif version == "v2":
                additional_output_id = "v2"

        assert model != "", "--model must be provided when --all_scenarios is 1"
        assert scenario_type != "", "--scenario_type must be provided when --all_scenarios is 1"
        assert additional_output_id != "", "--additional_output_id must be provided when --all_scenarios is 1"
        
        assert scenario_type in {"lm", "persistence", "exfiltration", "benign", "attack"}, "Value of scenario_type can only be one of the following: 'lm', 'persistece', 'exfiltration', 'benign', 'attack'"

        if allscenarios_type == "regular":
            outpath_list = get_outpathlist_regular(LLMOUTPUT_DIR, model, task, additional_output_id, scenario_type)
        elif allscenarios_type == "raw_equivalent":
            outpath_list = get_outpathlist_rawequivalent(LLMOUTPUT_DIR, dataset, model, task, additional_output_id, scenario_type)

    else:
        outpath = LLMOUTPUT_DIR+"/"+llmoutput_fname
        outpath_list.append((outpath, llmoutput_fname, LLMOUTPUT_DIR))

    """
    sorted_outpath_list is a sorted list consisting of 3-tuple with the following elements:
    1. full path of the output file
    2. file name of the output file
    3. directory path of the output file
    """
    sorted_outpath_list = sorted(outpath_list, key=get_scenario_number)

    return sorted_outpath_list


class TaskMetrics:
    
    precision_dict : dict[str, float]
    recall_dict : dict[str, float]
    fprate_dict : dict[str, float]
    accuracy_dict : dict[str, float]

    def __init__(self, task: str, version: str, sorted_outpath_list: list[(str, str, str)], dataset: str):
        self.task = task
        self.version = version
        self.sorted_outpath_list = sorted_outpath_list
        self.dataset = dataset

        self.input_fpaths = []

        self.precision_dict = {}
        self.recall_dict = {}
        self.fprate_dict = {}
        self.accuracy_dict = {}


    def compute_correctness(self, more_defensive=0) -> tuple[dict[str: int], dict[str, int], dict[str, float]]:
        """
        Computes correctness metric for multiple scenarios.
        Returns dictionaries: tp_scenarios, fp_scenarios, accuracy_scenarios containing
        TP, FP, accuracy respectively for scenarios
        """
        tp_scenarios = {}
        fp_scenarios = {}
        fn_scenarios = {}
        tn_scenarios = {}
        """accuracy_scenarios: dict # key = scenario identifier, value = (benign_dict, malicious_dict, accuracy_dict, total_chunks) """
        accuracy_scenarios = {}

        # Dynamic imports based on version
        try:
            modules = ModuleFactory(self.version)
        except ValueError as e:
            print(f"Error: {e}")
            exit(1)

        for outpath_tup in self.sorted_outpath_list:
            if self.task == "lm":
                obj = modules.ParserLateralMovement(self.dataset, self.task)
                llmresponse_dict, num_rounds = obj.parse_lateralmovement_llmoutput(outpath_tup[0])
            if self.task == "persistence":
                obj = modules.ParserPersistence(self.dataset, self.task)
                llmresponse_dict, num_rounds = obj.parse_persistence_llmoutput(outpath_tup[0])
            if self.task == "exfiltration":
                obj = modules.ParserExfiltration(self.dataset, self.task)
                llmresponse_dict, num_rounds = obj.parse_exfiltration_llmoutput(outpath_tup[0])
            if self.task == "classification":
                obj = modules.ParserClassification(self.dataset, self.task)
                llmresponse_dict, num_rounds = obj.parse_classification_llmoutput(outpath_tup[0])

            if self.dataset == "labgen":
                input_fname = "_".join(outpath_tup[1].split("_")[3:6])
            else:
                input_fname = "_".join(outpath_tup[1].split("_")[3:7]) 

            input_dir = "/".join(outpath_tup[2].split("/")[:4]+["input"])
            input_fpath = os.path.join(input_dir, input_fname)
            self.input_fpaths.append(input_fpath)

            #load ground truths
            groundtruth_key = get_groundtruth_key(outpath_tup, self.dataset)

            tn_scenarios[input_fname] = count_scenario_loglines(input_fpath)
            ei = modules.ErrorInvestigation(self.dataset, self.task)

            if self.task in {"lm", "persistence", "exfiltration"}:
            
                groundtruth_set = obj.read_task_groudtruth(groundtruth_key)

                #generate tp, fp, fn
                if self.version in {"v2"}:
                    fpresponse_dict, tpresponse_dict, fnresponse_dict, verdict_dict = ei.compute_confusionmatrix(llmresponse_dict, groundtruth_set, groundtruth_key, more_defensive)
                elif self.version in {"v1"}:
                    fpresponse_dict, tpresponse_dict, fnresponse_dict, verdict_dict = ei.compute_confusionmatrix(llmresponse_dict, groundtruth_set, groundtruth_key)

                if "benign" not in groundtruth_key:
                    #TODO: do not use the `compute_precision_recall` function. It doesn't compute the numbers correctly.
                    # precision, recall = metrics_comp_utils.compute_precision_recall(fpresponse_dict, tpresponse_dict, fnresponse_dict)

                    fp_scenarios[input_fname] = round(np.mean(ei.get_fpperround_from_dict(fpresponse_dict)), 2)
                    tp_scenarios[input_fname] = round(np.mean(ei.get_tpperround_from_dict(tpresponse_dict)), 2)
                    fn_scenarios[input_fname] = round(np.mean(list(fnresponse_dict.values())), 2)
                    tn_scenarios[input_fname] = round(tn_scenarios[input_fname] - fp_scenarios[input_fname], 2)

                    # logging.info("Precision: %s", precision)
                    # logging.info("Recall: %s", recall)

                    # self.precision_dict[input_fname] = precision
                    # self.recall_dict[input_fname] = recall

                else:
                    """For benign scenarios, fprate is a list containing total FPs in each round"""
                    fprate, _ = metrics_comp_utils.compute_precision_recall(fpresponse_dict, tpresponse_dict, fnresponse_dict)
                    # print("FP rate: ", fprate)
                
                    logging.info("FP rate: %s", fprate)
                    fp_scenarios[input_fname] = round(np.mean(fprate), 2)
                    tn_scenarios[input_fname] = round(tn_scenarios[input_fname] - fp_scenarios[input_fname], 2)
                    self.fprate_dict = fprate
            
            elif self.task == "classification":

                groundtruth_class = get_classification_gtclass(groundtruth_key)
                
                """
                benign_dict: dict # key - round number : value - number of chunks labelled benign
                malicous_dict: dict # key - round number : value - number of chunks labelled malicious
                """
                if self.version in {"v2"}:
                    benign_dict, malicious_dict, self.total_chunkcnt = ei.compute_chunkdecision(llmresponse_dict, more_defensive)
                elif self.version in {"v1"}:
                    benign_dict, malicious_dict, self.total_chunkcnt = ei.compute_chunkdecision(llmresponse_dict)
                accuracy_dict = metrics_comp_utils.compute_accuracy(benign_dict, malicious_dict, self.total_chunkcnt, groundtruth_class)
                logging.info("Accuracy: %s", accuracy_dict)
                """NOTE: for attack scenarios, the value of accuracy will either be 0 or 1 in a single round"""

                accuracy_scenarios[input_fpath] = (round(np.mean(list(benign_dict.values())), 2), 
                                                round(np.mean(list(malicious_dict.values())), 2), 
                                                round(np.mean(list(accuracy_dict.values())), 2), 
                                                self.total_chunkcnt)

                average_accuracy_across_rounds = round(np.mean(list(accuracy_dict.values())), 2)
                logging.info("Average accuracy across rounds: %s", average_accuracy_across_rounds)
                logging.info("Number of chunks: %s", self.total_chunkcnt)
                self.accuracy_dict = average_accuracy_across_rounds

                if groundtruth_class == "malicious":
                    tp_rounds = []
                    fn_rounds = []
                    for round_num in malicious_dict:
                        if malicious_dict[round_num] >= 1:
                            tp_rounds.append(1) #push 1 if the round is correctly predicted as malicious
                            fn_rounds.append(0)
                        else:
                            tp_rounds.append(0)
                            fn_rounds.append(1)
                    tp_scenarios[input_fname] = round(np.mean(tp_rounds), 2)
                    fn_scenarios[input_fname] = round(np.mean(fn_rounds), 2)
                elif groundtruth_class == "benign":
                    fp_rounds = []
                    tn_rounds = []
                    for round_num in malicious_dict:
                        fp_rounds.append(malicious_dict[round_num])
                        tn_rounds.append(benign_dict[round_num])
                    fp_scenarios[input_fname] = round(np.mean(fp_rounds), 2)
                    tn_scenarios[input_fname] = round(np.mean(tn_rounds), 2)
        
        return tp_scenarios, fp_scenarios, fn_scenarios, tn_scenarios, accuracy_scenarios

    def compute_aggregatecorrectness_scenariotype_task_rep(self, scenario_type: str, tp_scenarios: dict[str: float], fp_scenarios: dict[str: float], tn_scenarios: dict[str: int], fn_scenarios: dict[int: float], accuracy_scenarios: dict[str: float]) -> tuple[int, int, int, int] | tuple[int, int]:
        """
        returns the numerator and denominator for the tables.
        - For lm, persistence and exfil tasks, returns numerator and denominator for both TP and FP
        - For classification task, returns only one pair of numerator and denominator for either bengin or attack scenario
        """

        if self.dataset in {"labgen", "optc"} and (self.task in {"lm", "persistence", "exfiltration"}):
            aggregate_tp = count_aggregate_from_dict(tp_scenarios)
            aggregate_fp = count_aggregate_from_dict(fp_scenarios)
            aggregate_fn = count_aggregate_from_dict(fn_scenarios)
            aggregate_tn = count_aggregate_from_dict(tn_scenarios)

            gt_negatives = aggregate_tn + aggregate_fp
            gt_positives = aggregate_tp + aggregate_fn

            if "benign" not in scenario_type:
                logging.info("Aggregate LLM TPs: %s/%s = %s%%", aggregate_tp, gt_positives, round(aggregate_tp/gt_positives*100, 2))
            
            logging.info("Aggregate percentage LLM FPs: %s/%s = %s%%", aggregate_fp, gt_negatives, round(aggregate_fp/gt_negatives*100, 2))

            return aggregate_tp, gt_positives, aggregate_fp, gt_negatives

        elif self.dataset in {"labgen", "optc"} and self.task in {"classification"}:
            if "benign" in scenario_type:
                aggregate_chunks = 0
                aggregate_malicious_chunks = 0
                for scenario_fname,v in accuracy_scenarios.items():
                    aggregate_chunks += v[-1]
                    aggregate_malicious_chunks += v[1]
                
                logging.info("Aggregate FPs malicious labels: %s/%s=%s%%", aggregate_malicious_chunks, aggregate_chunks, round(aggregate_malicious_chunks/aggregate_chunks*100, 2))

                return aggregate_malicious_chunks, aggregate_chunks
            
            else:
                aggregate_accuracy = 0
                for scenario_fname,v in accuracy_scenarios.items():
                    aggregate_accuracy += v[2]
                logging.info("Aggregate LLM accuracy for ground truth attack scenarios: %s/%s=%s%%", aggregate_accuracy, len(accuracy_scenarios), round(aggregate_accuracy/len(accuracy_scenarios)*100, 2))

                return aggregate_accuracy, len(accuracy_scenarios)

        else:
            raise Exception("Invaid dataset or task.")



def tpr_fpr_computation_function_wrapper(task, version, sorted_outpath_list, dataset, more_defensive=0):
    taskmetric = TaskMetrics(task, version, sorted_outpath_list, dataset)
    tp_scenarios, fp_scenarios, fn_scenarios, tn_scenarios, accuracy_scenarios = taskmetric.compute_correctness(more_defensive)
    aggregate_tp, aggregate_fp = sum_tp_fp(tp_scenarios, fp_scenarios)
    aggregate_tn = 0
    aggregate_fn = 0
    
    # if task in {"lm", "persistence", "exfiltration"}:
    for fname, tn in tn_scenarios.items():
        aggregate_tn += tn
    for fname, fn in fn_scenarios.items():
        aggregate_fn += fn
    # elif task in {"classification"}:
        
    
    
    logging.info("Aggregate TP: ", aggregate_tp)
    logging.info("Aggregate FP: ", aggregate_fp)
    logging.info("Aggregate TN: ", aggregate_tn)
    logging.info("Aggregate FN: ", aggregate_fn)

    tpr = round(aggregate_tp/(aggregate_tp+aggregate_fn), 4) 
    fpr = round(aggregate_fp/(aggregate_fp+aggregate_tn), 4)
    if task == "classification":
        print("stats:", aggregate_tp, aggregate_fp, aggregate_tn, aggregate_fn)

    print("TPR: ", tpr)
    print("FPR: ", fpr)
    
    return aggregate_tp, aggregate_fp, aggregate_tn, aggregate_fn


def computation_function_wrapper(task, version, sorted_outpath_list, dataset, all_scenarios, scenario_type, rep, more_defensive=0):

    taskmetric = TaskMetrics(task, version, sorted_outpath_list, dataset)
    tp_scenarios, fp_scenarios, fn_scenarios, tn_scenarios, accuracy_scenarios = taskmetric.compute_correctness(more_defensive)

    """the compute_correctness function must be run before running compute_aggregate_scenariotype_task_rep function"""
    if all_scenarios:
        logging.info("\nPrinting aggregate stats for %s scenario type of %s task, %s representation:\n", scenario_type, task, rep)
    
        
        if task in {"lm", "persistence", "exfiltration"}:
            aggregate_tp, gt_positives, aggregate_fp, gt_negatives = taskmetric.compute_aggregatecorrectness_scenariotype_task_rep(scenario_type, tp_scenarios, fp_scenarios, tn_scenarios, fn_scenarios, accuracy_scenarios)
            logging.getLogger().functionprint(
                "%s, %s, %s, %s",
                aggregate_tp, gt_positives, aggregate_fp, gt_negatives
            )
            return aggregate_tp, gt_positives, aggregate_fp, gt_negatives
        
        elif task in {"classification"}:
            if scenario_type == "attack":
                aggregate_accuracy, aggregate_scenarios = taskmetric.compute_aggregatecorrectness_scenariotype_task_rep(scenario_type, tp_scenarios, fp_scenarios, tn_scenarios, fn_scenarios, accuracy_scenarios)
                logging.getLogger().functionprint(
                    "%s, %s",
                    aggregate_accuracy, aggregate_scenarios
                )
                return aggregate_accuracy, aggregate_scenarios
            
            elif scenario_type == "benign":
                aggregate_fp, aggregate_chunks = taskmetric.compute_aggregatecorrectness_scenariotype_task_rep(scenario_type, tp_scenarios, fp_scenarios, tn_scenarios, fn_scenarios, accuracy_scenarios)
                logging.getLogger().functionprint(
                    "%s, %s",
                    aggregate_fp, aggregate_chunks
                )
                return aggregate_fp, aggregate_chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="compute metrics for persistence task")
    parser.add_argument("--version", type=str, required=True, choices=list(PROMPT_VERSIONS) + list(LEGACY_PROMPT_VERSION_ALIASES),
                        help="The prompt version used during inference, which selects the parser modules: 'v1' (legacy) or 'v2' (current). "
                             "Legacy alias labels (see parser/customparser.py) are accepted and mapped to the current version.")
    parser.add_argument("--dataset", type=str, required=True, default="labgen", help="name of the dataset: 'labgen' or 'optc'")
    parser.add_argument("--metric", type=str, required=False, default="correctness",
                        help="metric to compute. 'correctness' (TP/FP/FN/TN counts and TPR/FPR) is the only metric implemented and is always computed; the flag is kept for backward compatibility")
    parser.add_argument("--rep", type=str, required=True,
                        help="one of 'raw', 'edge', 'graph'")
    parser.add_argument("--llm", type=str, required=True, default='gpt', help="LLM for running experiment")
    parser.add_argument("--llmoutput_fname", type=str, required=False,
                        help="optional argument to provide LLM output file name. If not given, evaluation will be done for all the files in the dir")
    parser.add_argument("--all_scenarios", type=str, required=False, default=0, help="set to 1 if want to calculate the \
                        metrics for all the LLM output files in a directory")
    parser.add_argument("--save_metrics", type=int, required=False, default=0, help="reserved; currently has no effect")
    parser.add_argument("--model", type=str, required=False, default="", help="model name for computing collective metrics")
    parser.add_argument("--scenario_type", type=str, required=False, default="", help="either 'benign' or 'attack'")
    parser.add_argument("--task", type=str, required=True, help="task name - either 'lm', 'persistence', 'exfiltration', or 'classification'")
    parser.add_argument("--quiet", type=int, required=False, default=0, help="set to 1 to suppress non-essential print statements")
    parser.add_argument("--more_defensive", type=int, required=False, default=0, help="set to 1 to be more defensive with v2 prompts.")

    
    args = parser.parse_args()

    requested_version = args.version
    args.version = normalize_prompt_version(args.version)
    if args.version != requested_version:
        print(f"[Warning] --version {requested_version!r} is a legacy label for prompt {args.version!r}; using {args.version!r}.", file=sys.stderr)

    sorted_outpath_list = computation_setup(args.version, args.dataset, args.rep, args.llm, args.llmoutput_fname, args.all_scenarios, args.model, args.scenario_type, args.task, args.quiet)

    computation_function_wrapper(args.task, args.version, sorted_outpath_list, args.dataset, args.all_scenarios, args.scenario_type, args.rep, args.more_defensive)
