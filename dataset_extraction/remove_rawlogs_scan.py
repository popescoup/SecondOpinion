import re
from tqdm import tqdm
import argparse
import os

def remove_scans(fpath):
    new_lines = []
    with open(fpath, 'r') as f:
        for line in f:
            if "terminal=ssh res=failed'" in line or "terminal=sshd res=failed'" in line:
                continue
            else:
                new_lines.append(line)
    return new_lines

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Remove scans from raw logs")
    parser.add_argument("--input_fpath", type=str, required=False, help='input raw logs')
    parser.add_argument("--task", type=str, required=False, help="one of 'detection', 'tampering', 'persistence', 'lateral movement")
    parser.add_argument("--all_files", type=int, required=False, default=0, help='set to 1 to remove scans from all files in the directory')
    parser.add_argument("--out_fpath", type=str, required=False, help='path of output logs')

    args = parser.parse_args()

    file_list = []

    if args.all_files:
        RAW_DIR=f"../scenarios/{args.task}/raw"
        for f in os.listdir(RAW_DIR):
            if os.path.isfile(os.path.join(RAW_DIR, f)) and f.endswith(".log"):
                file_list.append((os.path.join(RAW_DIR, f), f))
    else:
        # fpath = RAW_DIR+"/"+args.input_fpath
        fpath = args.input_fpath
        file_list.append((fpath, args.input_fpath))
    
    for obj in file_list:
        fpath = obj[0]
        new_lines = remove_scans(fpath)
        if not args.out_fpath:
            with open(fpath, 'w') as f:
                for line in tqdm(new_lines):
                    f.write(line)
        else:
            with open(args.out_fpath, "w") as f:
                for line in tqdm(new_lines):
                    f.write(line)