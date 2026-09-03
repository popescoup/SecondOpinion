from collections import defaultdict, deque
import numpy as np


class ErrorInvestigation:

    def __init__(self, dataset, task):
        self.dataset = dataset
        self.task = task

    def get_tpperround_from_dict(self, resultresponse_dict):
        """ Get just the count of TP from the tpresponse_dict.
        This function is intended to be used only for L.M., peristence and exifl tasks.
        """

        result_per_round = []
        if self.dataset == "optc" and self.task == "lm":
            for round_num in resultresponse_dict:
                unique_tpip_round = set()
                for chunk in resultresponse_dict[round_num]:
                    for elem in resultresponse_dict[round_num][chunk]:
                        unique_tpip_round.add(elem[2])
                result_per_round.append(len(unique_tpip_round))
        else:
            for round_num in resultresponse_dict:
                curr_round_result = 0
                if resultresponse_dict[round_num]:
                    for chunk in resultresponse_dict[round_num]:
                        #TODO: if in case exfiltration or peristence task also contains more than one
                        # attack instance within a scenario, then need to implement logic correctly 
                        # parse multiple persistence and/or exfiltration instances  
                        curr_round_result += len(resultresponse_dict[round_num][chunk])

                        if curr_round_result >= 1:
                            result_per_round.append(1)
                        else:
                            result_per_round.append(0)
                else:
                    result_per_round.append(0)
       
        return result_per_round

    def get_fpperround_from_dict(self, resultresponse_dict):
        """ Get just the count of FP from the fpresponse_dict.
        This function is intended to be used only for L.M., peristence and exifl tasks.
        """

        result_per_round = []
        for round_num in resultresponse_dict:
            curr_round_result = 0
            for chunk in resultresponse_dict[round_num]:
                curr_round_result += len(resultresponse_dict[round_num][chunk])
            result_per_round.append(curr_round_result)

        return result_per_round

    def compute_chunkdecision(self, llmresponse_dict) -> tuple[dict[int, int], dict[int, int], int]:
        """Returns benign_dict, malicious_dict, total_chunkcnt
        benign_dict - dictionary
            * key is round number, value is the number of benign labelled chunks
        malicious_dict - dictionary 
            * key is round round number, value is the number of malicious labelled chunks 
        total_chunkcnt: total number of chunks in the scenario
        """

        malicious_dict = defaultdict(int)
        benign_dict = defaultdict(int)

        for chunk_id, v in llmresponse_dict.items():
            for round_num, jsonout_list in v.items():
                if round_num not in malicious_dict:
                    malicious_dict[round_num] = 0
                if round_num not in benign_dict:
                    benign_dict[round_num] = 0

                if len(jsonout_list) == 0:
                    benign_dict[round_num] += 1
                else:
                    for tup in jsonout_list:
                        ocd = tup[-1].lower()
                        if ocd in {"malicious"}:
                            malicious_dict[round_num] += 1
                        elif ocd in {"benign"}:
                            benign_dict[round_num] += 1
                        else:
                            print("undefined overall classification decision: ", ocd)
        
        total_chunkcnt = len(llmresponse_dict)

        return benign_dict, malicious_dict, total_chunkcnt
    
    def find_llmout_in_groundtruth(self, candidate_tuple, groundtruth_set):
        llmout_ts = candidate_tuple[0]                    
        llmout_string = candidate_tuple[1].strip().lower()
        # print("Candidate: ", llmout_ts, llmout_string)

        for e in groundtruth_set:
            gt_elem2 = e[1].strip().lower()
            if gt_elem2 in llmout_string and e[0] == llmout_ts:
                return True
        return False

    def compute_confusionmatrix(self, llmresponse_dict, groundtruth_set, scenario) -> tuple [dict, dict] :
        """"
        scenario - string for hints about whether the llmresponse_dict is for a benign or attack scenario

        fpresponse_dict and tpresponse_dict stores for every round, a dictionry of chunk mapped to FP/TP outputs
        Key - round number
        Value - dictionary
            * Key of Value dictionary - chunk identifier
            * Value of Value dictionary - LLM generated FPs in the chunk
        """
        fpresponse_dict = defaultdict(dict)
        tpresponse_dict = defaultdict(dict)

        verdict_dict = defaultdict(dict)

        """
        fnrepsonse_dict saves the count of FNs per round
        Key: round
        Value: number of FNs in the round
        """
        fnresponse_dict = defaultdict()

        #For attack scenarios:
        if "benign" not in scenario:

            ## TP and FP computation:
            unique_host_intp = defaultdict(set)
            gt_unique_exthost = set()
            for chunk_id, v in llmresponse_dict.items():
                for round_num, jsonout_list in v.items():
                    if round_num not in fpresponse_dict:
                        fpresponse_dict[round_num] = defaultdict(list)
                    if round_num not in tpresponse_dict:
                        tpresponse_dict[round_num] = defaultdict(list)
                    if round_num not in unique_host_intp:
                        unique_host_intp[round_num] = set()
                    
                    for tup in jsonout_list:
                        #tup is all the output fields generated by the LLM and the round number

                        if tup:
                            candidate_tuple = (tup[1], tup[2])
                            if (tup[1], tup[2]) == ('', ''):
                                continue
                            
                            if self.task == "lm":
                                if candidate_tuple in groundtruth_set:
                                    tpresponse_dict[round_num][chunk_id].append(tup)
                                    #note that this tpresponse_dict will contain all the TPs found including repetitions!!
                                    unique_host_intp[round_num].add(tup[2])
                                else:
                                    fpresponse_dict[round_num][chunk_id].append(tup)
                            
                            if self.task == "persistence" or self.task == "exfiltration":
                                found = self.find_llmout_in_groundtruth(candidate_tuple, groundtruth_set)
                                if found:
                                    tpresponse_dict[round_num][chunk_id].append(tup)
                                else:
                                    fpresponse_dict[round_num][chunk_id].append(tup)
            
            ## FN Computation:
            if (self.dataset == "labgen" and self.task == "lm") or \
            self.task == "persistence" or \
                self.task == "exfiltration":
                """ 
                There is only 1 TP in labgen lateral movement scenarios. So there can be only 1 FN.
                Same logic for persistence task
                """
                for round_num, chunk_dict in tpresponse_dict.items():
                    tp_found = False
                    for chunk_id in chunk_dict:
                        if len(chunk_dict[chunk_id]) > 0:
                            tp_found = True
                            break
                    if tp_found == False:
                        fnresponse_dict[round_num] = 1
                    else:
                        fnresponse_dict[round_num] = 0
            
            if self.dataset == "optc" and self.task == "lm":
                # 1. First find the set of unique external hosts in ground truth
                # 2. Next find the set of unique external hosts in LLM output
                # 3. Substract set 1 - set 2 to get number of unique external hosts that are in ground
                #truth but not in LLM output. This gives the number of FPs
                for e in groundtruth_set:
                    gt_unique_exthost.add(e[1])

                for round_num, unique_tphost in unique_host_intp.items():
                    fn = len(gt_unique_exthost - unique_tphost)
                    fnresponse_dict[round_num] = fn

            ## print aggregate scenarios over all rounds:
            fp_rounds = []
            tp_rounds = []
            fn_rounds = []

            fp_rounds = self.get_fpperround_from_dict(fpresponse_dict)
            tp_rounds = self.get_tpperround_from_dict(tpresponse_dict)

            fn_rounds = list(fnresponse_dict.values())

            # print("Overall distinct FP count: ", len(overall_fp))
            print("Average FP count in LLM output: ", round(np.mean(fp_rounds), 2))
            print("Average FN count in LLM output: ", round(np.mean(fn_rounds), 2))
            print("Average TP count in LLM output: ", round(np.mean(tp_rounds), 2))

        
        # For benign scenarios:
        else:
            for chunk_id, v in llmresponse_dict.items():
                for round_num, jsonout_list in v.items():
                    
                    if round_num not in fpresponse_dict:
                        fpresponse_dict[round_num] = defaultdict(list)
                    
                    for tup in jsonout_list:
                        """All LLM outputs are FPs. No verdict field is present"""
                        # if tup[-1].lower() in {"high_suspicious", "medium_suspicious"}: 
                        fpresponse_dict[round_num][chunk_id].append(tup)

            ## Print false alarm stats
            false_alarms_per_round = self.get_fpperround_from_dict(fpresponse_dict)
            print("False alarms per round: ", false_alarms_per_round)
            if len(false_alarms_per_round) > 0:
                print("Average false alarms across rounds: ", round(np.mean(false_alarms_per_round), 2))
            else:
                print("Average false alarms across rounds: 0")
        
        return fpresponse_dict, tpresponse_dict, fnresponse_dict, verdict_dict