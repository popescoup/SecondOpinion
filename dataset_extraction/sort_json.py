import json
import argparse
from collections import defaultdict
from tqdm import tqdm
import datetime

def load_json(fpath):
    #handle the case of a replacement character
    parsed_lines = []
    with open(fpath, 'rb') as f:
        for i, line in enumerate(f, start=1):
            dec_line = line.decode('utf-8', errors='replace')
            if '�' in dec_line:
                print(f"Line {i} had invalid bytes, ignoring it:")
                print(dec_line.rstrip('\n'))
            else:
                parsed_lines.append(dec_line)
    
    json_parsed = ''.join(parsed_lines)
    data = json.loads(json_parsed)
    print(f"Total number of OPM elements in original data: {len(data)}")
    return data

def get_all_nodes(data):
    nodes = {}
    for d in tqdm(data):
        if d['type'] == "Process" or d['type'] == "Artifact" or d['type'] == "Agent":
            nodes[d['id']] = d
    return nodes

def sort_edges(data, os):
    print("Value of os: ", os)
    time_edge_map = defaultdict(list)
    for d in tqdm(data):
        if d['type'] != "Process" and d['type'] != "Artifact" and d['type'] != "Agent":
            if os == 'windows':
                ts_str = d['annotations']['datetime']
                time_edge_map[datetime.datetime.strptime(ts_str, "%m/%d/%Y %I:%M:%S %p").timestamp()].append(d)
            elif os == 'linux':
                time_edge_map[d['annotations']['time']].append(d)
            else:
                raise ValueError("Invalid value for os parameter")
    
    time_edge_map = {k:v for k,v in sorted(time_edge_map.items(), key=lambda x:x[0])}

    return time_edge_map

def write_sorted_edges_with_nodes(nodes, sorted_edges, out_fpath):
    written_nodeids = set()

    sorted_data = []
    for k, edges in sorted_edges.items():
        for e in edges:
            srcid = e['from']
            dstid = e['to']
            if srcid not in written_nodeids:
                written_nodeids.add(srcid)
                if srcid in nodes:
                    sorted_data.append(nodes[srcid])
            if dstid not in written_nodeids:
                written_nodeids.add(dstid)
                if dstid in nodes:
                    sorted_data.append(nodes[dstid])
            sorted_data.append(e)
    
    with open(out_fpath, 'w') as f:
        for e in sorted_data:
            jsonl_line = json.dumps(e)
            f.write(jsonl_line + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="sort the json file obtained from SPADE")
    parser.add_argument('--input_fpath', type=str, required=True,
                        help='file path of json file to sort')
    parser.add_argument('--out_fpath', type=str, required=False, default='../dataset/sorted_provenance.jsonl',
                        help='file path of sorted jsonl file')
    parser.add_argument('--system_os', type=str, required=False,
                        help="set to either 'linux' or 'windows' depending on whether to sort windows or linux logs.\
                            this is needed for parsing timestamps")
    
    args = parser.parse_args()

    data = load_json(args.input_fpath)

    nodes = get_all_nodes(data)
    sorted_edges = sort_edges(data, args.system_os)

    write_sorted_edges_with_nodes(nodes, sorted_edges, args.out_fpath)