from collections import defaultdict

def compute_precision_recall(fpresponse_dict, tpresponse_dict, fnresponse_dict):
    #TODO: do not use this implementatin. It doesn't count the TP and FP correctly
    # attack scenarios
    if fnresponse_dict:
        precision_round = []
        recall_round = []
        for round_num in fpresponse_dict:
            fp = 0
            tp = 0
            for chunk_id in fpresponse_dict[round_num]:
                fp += len(fpresponse_dict[round_num][chunk_id])
            for chunk_id in tpresponse_dict[round_num]:
                tp += len(tpresponse_dict[round_num][chunk_id])
            
            fn = fnresponse_dict[round_num]

            if tp+fp > 0:
                precision = round(tp/(tp+fp), 2)
            else:
                precision = 0
            
            recall = round(tp/(tp+fn), 2)
            
            precision_round.append(precision)
            recall_round.append(recall)
        
        return precision_round, recall_round
    
    # benign scenarios
    else:
        fprate_round = []
        for round_num in fpresponse_dict:
            fp = 0
            for chunk_id in fpresponse_dict[round_num]:
                fp += len(fpresponse_dict[round_num][chunk_id])

            fprate_round.append(fp)
        
        return fprate_round, None
    
def compute_accuracy(
    benign_dict: dict[int, int],
    malicious_dict: dict[int, int],
    total_chunkcnt: int,
    groundtruth_class: str
) -> dict[int, float]:
    
    accuracy_dict = defaultdict()
    for round_num in malicious_dict:
        if groundtruth_class == "benign":
            accuracy_dict[round_num] = round(benign_dict[round_num]/total_chunkcnt, 2)
        else:
            if malicious_dict[round_num] >= 1:
                accuracy_dict[round_num] = 1
            else:
                accuracy_dict[round_num] = 0
    
    return accuracy_dict