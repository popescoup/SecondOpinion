import argparse
import json
from tqdm import tqdm
import os

process_attr = ["pid", "commandline", "imagepath"]
agent_attr = ["User"]
file_attr = ["path"]
file_system_attr = ["path"]
registry_attr = ["path"]
network_attr = ["remote host", "remote port", "local host", "local port"]
edge_attr = ["datetime", "operation"]

def construct_node_struct(inp):
    nodes_dict = {}
    with open(inp, 'r') as f:
        for line in tqdm(f):
            d = json.loads(line)
            if d['type'] == "Process":
                id = d['id']
                nodes_dict[id] = {}
                nodes_dict[id]['type'] = 'process'
                for e in process_attr:
                    nodes_dict[id][e] = d['annotations'][e]
            
            if d['type'] == "Artifact":
                id = d['id']
                nodes_dict[id] = {}
                if 'subtype' in d['annotations']:
                    if d['annotations']['subtype'] == "file":
                        nodes_dict[id]['type'] = "file"
                        for e in file_attr:
                            nodes_dict[id][e] = d['annotations'][e]
                    
                    if d['annotations']['subtype'] == "network":
                        nodes_dict[id]['type'] = "network"
                        for e in network_attr:
                            if e == 'local host':
                                nodes_dict[id][e] = 'localhost'
                            else:
                                nodes_dict[id][e] = d['annotations'][e]

                if 'class' in d['annotations']:
                    if d['annotations']['class'] == "File System":
                        nodes_dict[id]['type'] = "file"
                        for e in file_system_attr:
                            nodes_dict[id][e] = d['annotations'][e]
                    
                    if d['annotations']['class'] == "Registry":
                        nodes_dict[id]['type'] = "registry"
                        for e in registry_attr:
                            nodes_dict[id][e] = d['annotations'][e]
                
            if d['type'] == "Agent":
                id = d['id']
                nodes_dict[id] = {}
                nodes_dict[id]['type'] = 'agent'
                for e in agent_attr:
                    nodes_dict[id][e] = d['annotations'][e]

    return nodes_dict

def construct_reduced_edge(inp):
    nodes_dict = construct_node_struct(inp)

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
                
                edge_key_val_attr = {}
                edge_key_val_attr['type'] = d['type']
                edge_ts = d['annotations']['datetime']

                edge_op = None
                edge_type = d["type"]

                if 'operation' in d['annotations']:
                    edge_key_val_attr['operation'] = d['annotations']['operation']
                    edge_op = d['annotations']['operation']

                object_1_attr = nodes_dict[object_1]
                object_2_attr = nodes_dict[object_2]

                srcid = None
                src_attr = None
                dstid = None
                dst_attr = None

                if edge_op != None:
                    if edge_op in {"RegCreateKey", "RegSetValue", "RegDeleteKey", "RegDeleteValue",}:
                        if object_1_attr["type"] == "process" and object_2_attr["type"] == "registry":
                            srcid = object_1
                            src_attr = object_1_attr
                            dstid = object_2
                            dst_attr = object_2_attr
                        elif object_1_attr["type"] == "registry" and object_2_attr["type"] == "process":
                            srcid = object_2
                            src_attr = object_2_attr
                            dstid = object_1
                            dst_attr = object_1_attr
                    
                    if edge_op in {"TCP Receive", "UDP Receive"}:
                        if object_1_attr["type"] == "network" and object_2_attr["type"] == "process":
                            srcid = object_1
                            src_attr = object_1_attr
                            dstid = object_2
                            dst_attr = object_2_attr
                        elif object_1_attr["type"] == "process" and object_2_attr["type"] == "network":
                            srcid = object_2
                            src_attr = object_2_attr
                            dstid = object_1
                            dst_attr = object_1_attr
                    
                    if edge_op in {"Load Image",}:
                        if object_1_attr["type"] == "file" and object_2_attr["type"] == "process":
                            srcid = object_1
                            src_attr = object_1_attr
                            dstid = object_2
                            dst_attr = object_2_attr
                        elif object_1_attr["type"] == "process" and object_2_attr["type"] == "file":
                            srcid = object_2
                            src_attr = object_2_attr
                            dstid = object_1
                            dst_attr = object_1_attr
                    
                    if edge_op in {"WriteFile", "CreateFile", "SetRenameInformationFile"}:
                        if object_1_attr["type"] == "process" and object_2_attr["type"] == "file":
                            srcid = object_1
                            src_attr = object_1_attr
                            dstid = object_2
                            dst_attr = object_2_attr
                        elif object_1_attr["type"] == "file" and object_2_attr["type"] == "process":
                            srcid = object_2
                            src_attr = object_2_attr
                            dstid = object_1
                            dst_attr = object_1_attr

                    if edge_op in {"UDP Send", "TCP Connect"}:
                        if object_1_attr["type"] == "process" and object_2_attr["type"] == "network":
                            srcid = object_1
                            src_attr = object_1_attr
                            dstid = object_2
                            dst_attr = object_2_attr
                        elif object_1_attr["type"] == "network" and object_2_attr["type"] == "process":
                            srcid = object_2
                            src_attr = object_2_attr
                            dstid = object_1
                            dst_attr = object_1_attr

                else:
                    if edge_type == "WasTriggeredBy": # process - process edge
                        srcid = object_2
                        src_attr = object_2_attr
                        dstid = object_1
                        dst_attr = object_1_attr
                    
                    elif edge_type == "WasControlledBy": # agent - process edge
                        if object_1_attr["type"] == "process" and object_2_attr["type"] == "agent":
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
    print("number of reduced edges: ")
    print(len(reduced_edges))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        for e in tqdm(reduced_edges):
            f.write(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Find edge representation from SPADE output of Windows logs")
    parser.add_argument("--input_fpath", type=str, required=True, help='path of SPADE json data')
    parser.add_argument("--out_fpath", type=str, required=False, help='path of reduced edge representation')

    args = parser.parse_args()
    reduced_edges = construct_reduced_edge(args.input_fpath)
    if args.out_fpath:
        write_reduced_edges(args.out_fpath, reduced_edges)