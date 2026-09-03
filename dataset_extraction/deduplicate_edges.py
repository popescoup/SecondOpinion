import re
from collections import defaultdict
from tqdm import tqdm
import argparse

def deduplicate_edges(fpath, system_os):
    deduplicated_edge_set = set()
    deduplicated_edges = []
    if system_os == "windows":
        print("Reducing Windows edges")
        with open(fpath, 'r') as f:
            for line in tqdm(f):
                l = line.split("-->")
                src = l[0]
                edgestr = l[1]
                dst = l[2]
                match = re.search(r"{.*?}", edgestr)
                edge = match.group(0)
                new_tup = (src, edge, dst)
                if new_tup not in deduplicated_edge_set:
                    deduplicated_edge_set.add(new_tup)
                    deduplicated_edges.append(f"{src} --> {edgestr} --> {dst}")
    elif system_os == "linux":
        print("Reducing Linux edges")
        with open(fpath, 'r') as f:
            for line in tqdm(f):
                l = line.split("-->")
                src = l[0]
                edgestr = l[1]
                dst = l[2]
                match = re.search(r"{.*?}", edgestr)
                ts = re.search(r"\((.*?)\)", src).group(1)
                parts = re.split("\((.*?)\)\s", src, maxsplit=1)
                newts = str(float(ts))
                newsrc = f"({newts}) " + parts[2]
                new_tup = (newsrc, edgestr, dst)
                if new_tup not in deduplicated_edge_set:
                    deduplicated_edge_set.add(new_tup)
                    deduplicated_edges.append(f"{newsrc} --> {edgestr} --> {dst}")
    
    return deduplicated_edges

def write_edges(edges, outpath):
    print("Writing deduplicated edges")
    with open(outpath, 'w') as f:
        for e in edges:
            f.write(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("De-duplicated edge representation")
    parser.add_argument("--input_fpath", type=str, required=True, help='input edge representation')
    parser.add_argument("--out_fpath", type=str, required=False, help='output edge representation')
    parser.add_argument("--system_os", type=str, required=False, default="windows", help="either windows or linux dataset")

    args = parser.parse_args()

    deduplicated_edges = []
    deduplicated_edges = deduplicate_edges(args.input_fpath, args.system_os)

    if args.out_fpath:
        write_edges(deduplicated_edges, args.out_fpath)
