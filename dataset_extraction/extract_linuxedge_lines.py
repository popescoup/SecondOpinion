import argparse
import datetime
from tqdm import tqdm
import re
import pytz
import deduplicate_edges as de

def extract_edge_logs(fpath, start_time, end_time):
    outlines = []
    with open(fpath, 'r') as f:
        for line in tqdm(f):
            found = re.search(r"\((.*?)\)", line)
            line_ts = float(found.group(1))
            if line_ts >= start_time and line_ts < end_time:
                outlines.append(line)
    return outlines

def write_extracted_logs(edge_lines, outfpath):
    with open(outfpath, 'w') as f:
        for e in tqdm(edge_lines):
            f.write(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("extract edges given input start and end timestamps")
    parser.add_argument("--start_time", type=str, required=True, help="start timestamp of logs in the format 'YYYY-MM-DD HH:MM' ")
    parser.add_argument("--end_time", type=str, required=True, help="end timestamp of logs")
    parser.add_argument("--input_fpath", type=str, required=True, help="path of input log file")
    parser.add_argument("--out_fpath", type=str, required=False, help="path to save the extracted logs")
    parser.add_argument("--system_os", type=str, required=True, help="system_os for deduplication. Most of the times it is generally linux because windows logs are deduplicated by the spade-json-to-edge.sh")

    args = parser.parse_args()

    # Use Chicago timezone in our case
    chicago_tz = pytz.timezone('US/Central')

    start_dtobj = datetime.datetime.strptime(args.start_time, "%Y-%m-%d %H:%M")
    start_dtobj = chicago_tz.localize(start_dtobj)
    start_unix = start_dtobj.timestamp()

    end_dtobj = datetime.datetime.strptime(args.end_time, "%Y-%m-%d %H:%M")
    end_dtobj = chicago_tz.localize(end_dtobj)
    end_unix = end_dtobj.timestamp()

    extracted_edges = extract_edge_logs(args.input_fpath, start_unix, end_unix)

    print("Number of extracted edges: ", len(extracted_edges))
    if args.out_fpath:
        write_extracted_logs(extracted_edges, args.out_fpath)
        
        deduplicated_edges = de.deduplicate_edges(args.out_fpath, args.system_os)
        de.write_edges(deduplicated_edges, args.out_fpath)