import pandas as pd

def sum_tp_fp(tp_scenarios, fp_scenarios):
    """generate sum of TPs and FPs for all 5 scenarios"""
    sum_fp = 0
    sum_tp = 0
    for fname, tpcnt in tp_scenarios.items():
        sum_tp += tpcnt
    for fname, fpcnt in fp_scenarios.items():
        sum_fp += fpcnt
    
    return sum_tp, sum_fp


def count_aggregate_from_dict(scenarios):
    """
    counts the sum of values of the dictionary
    scenarios - dictionary of {fname: either TN or FN}
    """
    cnt = 0
    for fname, val in scenarios.items():
        cnt += val
    return cnt