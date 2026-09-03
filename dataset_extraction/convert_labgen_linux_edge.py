import argparse
import json
from tqdm import tqdm
import os

process_attr = ["pid", "uid", "exe", "name", "command line", "cwd"]
file_attr = ["path", "permissions", "version"]
sock_attr = ["remote address", "remote port", "epoch"]
dir_attr = ["path", "permissions", "version"]

def construct_node_struct(inp, new_artifact_op='exclude'):
    print("Constructing node list")
    nodes_dict = {}
    with open(inp, 'r') as f:
        for line in tqdm(f):
            d = json.loads(line)
            if d['type'] == "Process":
                id = d['id']
                nodes_dict[id] = {}
                nodes_dict[id]['type'] = 'process'
                for e in process_attr:
                    if e not in d['annotations']:
                        continue
                    nodes_dict[id][e] = d['annotations'][e]
            if d['type'] == "Artifact":
                id = d['id']
                nodes_dict[id] = {}
                if d['annotations']['subtype'] == "file":
                    nodes_dict[id]['type'] = 'file'
                    for e in file_attr:
                        nodes_dict[id][e] = d['annotations'][e]
                elif d['annotations']['subtype'] == 'network socket':
                    nodes_dict[id]['type'] = 'network socket'
                    for e in sock_attr:
                        nodes_dict[id][e] = d['annotations'][e]
                elif d['annotations']['subtype'] == 'directory':
                    nodes_dict[id]['type'] = 'directory'
                    for e in dir_attr:
                        nodes_dict[id][e] = d['annotations'][e]
                #previously unseen subtype - 2 options: inclusion, exclusion
                else:
                    #inclusion - all attributes
                    if new_artifact_op == 'include':
                        for attr in d['annotations']:
                            nodes_dict[id][attr] = d['annotations'][attr]
                    #exclusion
                    if new_artifact_op == 'exclude':
                        del nodes_dict[id]

    return nodes_dict

def construct_edgerep(inp, new_artifacts_op): 
    nodes_dict = construct_node_struct(inp, new_artifacts_op)

    reduced_edges = []
    edgecnt = 0
    with open(inp, 'r') as f:
        for line in tqdm(f):
            d = json.loads(line)
            if d['type'] != "Process" and d['type'] != "Artifact" and d['type'] != "Agent":
                edgeid = f"e{edgecnt}"
                edgecnt += 1

                object_1 = d['from']
                object_2 = d['to']

                if (object_1 not in nodes_dict) or (object_2 not in nodes_dict):
                    continue
                
                edge_ts = d['annotations']['time']
                
                edge_key_val_attr = {}
                edge_key_val_attr["type"] = d['type']
                edge_key_val_attr["operation"] = d['annotations']['operation']
                edge_key_val_attr["event id"] = d['annotations']['event id']

                if 'size' in d['annotations']:
                    edge_key_val_attr["size"] = d['annotations']['size']
                if 'mode' in d['annotations']:
                    edge_key_val_attr["mode"] = d['annotations']['mode']

                object_1_attr = nodes_dict[object_1]
                object_2_attr = nodes_dict[object_2]

                edge_op = d["annotations"]["operation"]
                edge_type = d["type"]

                srcid = None
                src_attr = None
                dstid = None
                dst_attr = None


                if (edge_op in {"load", "rename (read)"}) or (edge_op == "open" and edge_type == "Used"):
                    if (object_1_attr["type"] in {"file", "directory"}) and object_2_attr["type"] == "process":
                        srcid = object_1
                        src_attr = object_1_attr
                        dstid = object_2
                        dst_attr = object_2_attr
                    elif object_1_attr["type"] == "process" and (object_2_attr["type"] in {"file", "directory"}):
                        srcid = object_2
                        src_attr = object_2_attr
                        dstid = object_1
                        dst_attr = object_1_attr
                
                if (edge_op in {"chmod", "rename (write)", "unlink", "close", "create"}) or (edge_op == "open" and edge_type == "WasGeneratedBy"):
                    if object_1_attr["type"] == "process" and (object_2_attr["type"] in {"file", "directory"}):
                        srcid = object_1
                        src_attr = object_1_attr
                        dstid = object_2
                        dst_attr = object_2_attr
                    elif (object_1_attr["type"] in {"file", "directory"}) and object_2_attr["type"] == "process":
                        srcid = object_2
                        src_attr = object_2_attr
                        dstid = object_1
                        dst_attr = object_1_attr

                if edge_op in {"execve", "rename", "update", "fork"}: #both objects are same type but reversed in provenance-graph
                    if object_1_attr["type"] in {"process", "network socket", "file", "directory"} and object_2_attr["type"] in {"process", "network socket", "file", "directory"}:
                        srcid = object_2
                        src_attr = object_2_attr
                        dstid = object_1
                        dst_attr = object_1_attr
                
                if edge_op in {"connect", "close"}:
                    if object_1_attr["type"] == "process" and object_2_attr["type"] == "network socket":
                        srcid = object_1
                        src_attr = object_1_attr
                        dstid = object_2
                        dst_attr = object_2_attr
                    elif object_1_attr["type"] == "network socket" and object_2_attr["type"] == "process":
                        srcid = object_2
                        src_attr = object_2_attr
                        dstid = object_1
                        dst_attr = object_1_attr
                
                if edge_op in {"accept"}:
                    if object_1_attr["type"] == "network socket" and object_2_attr["type"] == "process":
                        srcid = object_1
                        src_attr = object_1_attr
                        dstid = object_2
                        dst_attr = object_2_attr
                    elif object_1_attr["type"] == "process" and object_2_attr["type"] == "network socket":
                        srcid = object_2
                        src_attr = object_2_attr
                        dstid = object_1
                        dst_attr = object_1_attr

                if srcid and dstid and src_attr and dst_attr:
                    edge = f"({edge_ts})" + f" [{srcid}]" + str(src_attr) + " --> " + f"[{edgeid}]" + \
                        str(edge_key_val_attr) + " --> " + f"[{dstid}]" + str(dst_attr) + "\n"
                    reduced_edges.append(edge)

    return reduced_edges
    
def write_reduced_edges(out, reduced_edges):
    print("number of edges: ")
    print(len(reduced_edges))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        for e in tqdm(reduced_edges):
            f.write(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Find edge representation from SPADE output")
    parser.add_argument("--input_fpath", type=str, required=True, help='path of sorted SPADE jsonl file')
    parser.add_argument("--out_fpath", type=str, required=False, help='path of reduced edge representation')
    parser.add_argument("--new_artifacts_op", type=str, required=False, default='exclude', help='set to include to \
                        inlcude all the annotations of previously unseen nodes in reduced edge represetnation. \
                        "exclude" will exclude the previously unseen nodes entirely')

    args = parser.parse_args()
    reduced_edges = construct_edgerep(args.input_fpath, args.new_artifacts_op)
    if args.out_fpath:
        write_reduced_edges(args.out_fpath, reduced_edges)
