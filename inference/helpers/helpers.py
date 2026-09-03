import re
import ast
import igraph as ig
import os
import pickle
import datetime
import json

def parse_edgerep_line(line):
    line = line.strip("\n")
    l = line.split(" --> ")
    source_part = l[0]
    edge = l[1]
    dst_part = l[2]
    
    ts = re.search(r"\((.*?)\)", source_part).group(1)
    src_id = re.search(r"\[(.*?)\]", source_part).group(1)
    src_attr = re.search(r"\{(.*)\}", source_part).group(0)
    src_attr_dict = ast.literal_eval(src_attr)

    edge_id = re.search(r"\[(.*?)\]", edge).group(1)
    edge_attr = re.search(r"\{(.*)\}", edge).group(0)
    edge_attr_dict = ast.literal_eval(edge_attr)

    dst_id = re.search(r"\[(.*?)\]", dst_part).group(1)
    dst_attr = re.search(r"\{(.*)\}", dst_part).group(0)
    dst_attr_dict = ast.literal_eval(dst_attr)

    return (ts, src_id, src_attr_dict, edge_id, edge_attr_dict, dst_id, dst_attr_dict)

def create_graph(edge_path, dataset):
    if dataset == "optc":
        print(f"Creating graph for {edge_path}")
        unique_nodes_idxmap = {}
        edges = []
        edge_attributes = []
        vcnt = 0
        index = 0
        with open(edge_path, 'r') as f:
            for line in f:
                try:
                    l = parse_edgerep_line(line)
                    if len(l) == 7:
                        if l[1] not in unique_nodes_idxmap:
                            unique_nodes_idxmap[l[1]] = index
                            unique_nodes_idxmap[index] = (l[1], l[2])
                            vcnt += 1
                            index += 1
                        if l[5] not in unique_nodes_idxmap:
                            unique_nodes_idxmap[l[5]] = index
                            unique_nodes_idxmap[index] = (l[5], l[6])
                            index += 1
                            vcnt += 1
                        edges.append((unique_nodes_idxmap[l[1]], unique_nodes_idxmap[l[5]]))
                        edge_attr_tmp = l[4]
                        edge_attr_tmp['timestamp'] = l[0]
                        edge_attr_tmp['edge id'] = l[3]
                        edge_attributes.append(edge_attr_tmp)
                    else:
                        print("Length of this list is not 7: ", l)
                except:
                    print(line)
        
        #create graph object
        g = ig.Graph(directed=True)
        g.add_vertices(vcnt)
        g.add_edges(edges)

        #add node attributes
        for v in g.vs:
            g.vs[v.index]["UUID"] = unique_nodes_idxmap[v.index][0]
            for key, val in unique_nodes_idxmap[v.index][1].items():
                g.vs[v.index][key] = val

        #add edge attributes
        for e in g.es:
            for key, val in edge_attributes[e.index].items():
                g.es[e.index][key] = val
        return g
    
def save_igraph(g, fpath): #putting this function here and not in helpers.py because currently passing relative path
    print("Is the new graph directed? ", g.is_directed())
    
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    with open(fpath, 'wb') as f:
        pickle.dump(g, f)
    # with lzma.open(fpath, 'wb') as f:
    #     pickle.dump(g, f)

def unixts_to_string(unixts):
    dt_obj = datetime.datetime.fromtimestamp(unixts)
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S")

def create_output_filename(prompt_key, log_fpath, date, temp, num_runs, model_name, other_llm_param=''):
    if "/" in model_name:
        model_name = model_name.replace("/", "-")
    prompt_type = prompt_key.split("_")[0]
    prompt_version = prompt_key.split("_")[1]
    log_fname = log_fpath.split("/")[-1]
    if other_llm_param == '':
        outfpath = f"{prompt_type}_{prompt_version}_{model_name}_{log_fname}_{date}_temp-{temp}_numruns-{num_runs}.txt"
    else:
        outfpath = f"{prompt_type}_{prompt_version}_{model_name}_{log_fname}_{date}_temp-{temp}_numruns-{num_runs}_otherparam-{other_llm_param}.txt"
    return outfpath

def write_output(result, outpath, start_linenum, num_lines, llm='gpt', misc=''):
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'a') as f:
        f.write('\n\n')
        f.write(f"****Starting line num: {start_linenum}. Num lines: {num_lines}. {misc}****\n\n")
        f.write(result)
        f.write('\n\n')
        f.write(f'-----------------------{llm}------------------------\n')

def load_gpt_security_prompt(key, BENCHMARK_GPT_PROMPT_FILE):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.abspath(os.path.join(curr_dir, BENCHMARK_GPT_PROMPT_FILE))
    with open(full_path, 'r') as f:
        for line in f:
            d = json.loads(line, strict=False)
            for k in d:
                if k == key:
                    return d[k]
                
def load_gemini_security_prompt(key, BENCHMARK_GEMINI_PROMPT_FILE):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.abspath(os.path.join(curr_dir, BENCHMARK_GEMINI_PROMPT_FILE))
    with open(full_path, 'r') as f:
        for line in f:
            d = json.loads(line, strict=False)
            for k in d:
                if k == key:
                    return d[k]
    return None
                
def load_logs(fpath, stidx, enidx):
    data = []
    with open(fpath, 'r') as f:
        for idx, line in enumerate(f):
            if idx >= stidx and idx <= enidx:
                data.append(line)
    return data

def parse_edgerep_line(line):
    line = line.strip("\n")
    l = line.split(" --> ")
    source_part = l[0]
    edge = l[1]
    dst_part = l[2]
    
    ts = re.search(r"\((.*?)\)", source_part).group(1)
    src_id = re.search(r"\[(.*?)\]", source_part).group(1)
    src_attr = re.search(r"\{(.*)\}", source_part).group(0)
    src_attr_dict = ast.literal_eval(src_attr)

    edge_id = re.search(r"\[(.*?)\]", edge).group(1)
    edge_attr = re.search(r"\{(.*)\}", edge).group(0)
    edge_attr_dict = ast.literal_eval(edge_attr)

    dst_id = re.search(r"\[(.*?)\]", dst_part).group(1)
    dst_attr = re.search(r"\{(.*)\}", dst_part).group(0)
    dst_attr_dict = ast.literal_eval(dst_attr)

    return (ts, src_id, src_attr_dict, edge_id, edge_attr_dict, dst_id, dst_attr_dict)
