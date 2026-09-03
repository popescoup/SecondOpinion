import argparse
import datetime
from tqdm import tqdm
from collections import defaultdict
import re
from typing import List, Tuple

def parse_auditd_timestamp(timestamp_str: str) -> float:
    """
    Extract timestamp from auditd log message.
    
    Args:
        timestamp_str (str): Timestamp string from auditd log
    
    Returns:
        float: Parsed Unix timestamp
    """
    match = re.search(r'audit\((\d+\.\d+):', timestamp_str)
    if match:
        return float(match.group(1))
    return -1


def filter_log_by_ranges(
    input_log_path: str, 
    timestamp_ranges: List[Tuple[float, float]], 
    output_prefix: str = 'auditd_data_tampering_'
) -> None:
    """
    Filter log file based on multiple timestamp ranges.
    
    Args:
        input_log_path (str): Path to the input log file
        timestamp_ranges (List[Tuple[float, float]]): List of (start, end) timestamp ranges
        output_prefix (str, optional): Prefix for output filenames
    """
    # Validate input
    if not timestamp_ranges:
        raise ValueError("At least one timestamp range must be provided")
    
    # Prepare output files
    output_files = [
        open(f"{output_prefix}{i+1}.log", 'w') 
        for i in range(len(timestamp_ranges))
    ]
    
    try:
        with open(input_log_path, 'r') as input_file:
            for line in input_file:
                # Extract timestamp from the line
                timestamp = parse_auditd_timestamp(line)
                
                # Check against each range and write to corresponding file
                for i, (start, end) in enumerate(timestamp_ranges):
                    if start <= timestamp <= end:
                        output_files[i].write(line)
    
    except IOError as e:
        print(f"Error processing log file: {e}")
    
    finally:
        # Close all output files
        for file in output_files:
            file.close()
    
    print(f"Log filtering complete. {len(timestamp_ranges)} output files created.")

def extract_logs(fpath, start_time, end_time):
    outlines = defaultdict(list)
    with open(fpath, 'r') as f:
        for line in tqdm(f):
            l = line.split(" ")
            for e in l:
                key_val = e.split("=")
                key = key_val[0]
                val = key_val[1]
                if key == "msg":
                    found = re.findall(r"audit\((.*?):(.*?)\):", val)
                    line_ts = float(found[0][0])
                    if line_ts >= start_time and line_ts < end_time:
                        outlines[line_ts].append(line)
                    break

    outlines = {k:v for k,v in sorted(outlines.items(), key=lambda x:x[0])}
    return outlines

def write_extracted_logs(ts_loglines_dict, fpath):
    with open(fpath, 'w') as f:
        for k,v in ts_loglines_dict.items():
            for line in v:
                f.write(line)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("extract auditd log lines given input start and end timestamps")
    parser.add_argument("--start_time", type=str, required=True, help="start timestamp of logs in the format 'YYYY-MM-DD HH:MM' ")
    parser.add_argument("--end_time", type=str, required=True, help="end timestamp of logs")
    parser.add_argument("--input_fpath", type=str, required=True, help="path of input log file")
    parser.add_argument("--out_fpath", type=str, required=False, help="path to save the extracted logs")
    parser.add_argument("--query_range", type=int, required=False, default=0, help="set to 1 to extract log lines fromi a range of timestamps")

    args = parser.parse_args()

    start_dtobj = datetime.datetime.strptime(args.start_time, "%Y-%m-%d %H:%M")
    start_unix = start_dtobj.timestamp()

    end_dtobj = datetime.datetime.strptime(args.end_time, "%Y-%m-%d %H:%M")
    end_unix = end_dtobj.timestamp()

    if args.query_range == 0:
        relevant_logs_tsdict = extract_logs(args.input_fpath, start_unix, end_unix)
        if args.out_fpath:
            write_extracted_logs(relevant_logs_tsdict, args.out_fpath)

    elif args.query_range == 1:
        ranges = [
            (1730104560, 1730105100),  
            (1730116980, 1730119140),  
            (1730133660, 1730135220),  
            (1730135880, 1730136180),  
            (1730136540, 1730137740)   
        ]
        
        filter_log_by_ranges(
            input_log_path='/path/to/audit.log',
            timestamp_ranges=ranges
        )