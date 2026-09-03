import re
from collections import defaultdict
from tqdm import tqdm
import argparse
import datetime
import deduplicate_edges as de

def get_trimmed_edges(fpath, start_ts, end_ts):
    trimmed_edges = []
    with open(fpath, 'r') as f:
        for line in tqdm(f):
            l = line.split("-->")
            src = l[0]
            ts_str = re.search(r"\((.*?)\)", src).group(1)
            ts = datetime.datetime.strptime(ts_str, "%m/%d/%Y %I:%M:%S %p").timestamp()
            if ts >= start_ts and ts < end_ts:
                trimmed_edges.append(line)
    return trimmed_edges

def write_edges(edges, fpath):
    with open(fpath, 'w') as f:
        for edge in edges:
            f.write(edge)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("De-duplicated edge representation")
    parser.add_argument("--input_fpath", type=str, required=True, help='input edge representation')
    parser.add_argument("--out_fpath", type=str, required=False, help='output edge representation')
    parser.add_argument("--system_os", type=str, required=False, default="windows", help="either windows or linux dataset")
    parser.add_argument("--start_ts", type=str, required=False, help="start time for trimming in the format YYYY-MM-DD HH:MM")
    parser.add_argument("--end_ts", type=str, required=False, help="end time for trimming in the format YYYY-MM-DD HH:MM")

    args = parser.parse_args()

    start_ts = datetime.datetime.strptime(args.start_ts, "%Y-%m-%d %H:%M").timestamp()
    end_ts = datetime.datetime.strptime(args.end_ts, "%Y-%m-%d %H:%M").timestamp()
    
    print(start_ts)
    print(end_ts)

    trimmed_edges = get_trimmed_edges(args.input_fpath, start_ts, end_ts)
    print(f"{len(trimmed_edges)=}")

    if args.out_fpath:
        write_edges(trimmed_edges, args.out_fpath)

        deduplicated_edges = de.deduplicate_edges(args.out_fpath, args.system_os)
        de.write_edges(deduplicated_edges, args.out_fpath)