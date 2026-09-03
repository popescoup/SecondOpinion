import re
from tqdm import tqdm
import argparse

def remove_keys(fpath, system_os):
    modified_logs = []
    if system_os == "linux":
        with open(fpath, 'r') as f:
            for line in tqdm(f):
                l = line.split()
                for e in l:
                    if bool(re.match(r"^key=", e)):
                        l.remove(e)
                lstr = " ".join(l)
                modified_logs.append(lstr)
    return modified_logs

def write_logs(logs, fpath):
    with open(fpath, 'w') as f:
        for line in tqdm(logs):
            f.write(line)
            f.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Remove keys from log")
    parser.add_argument("--input_fpath", type=str, required=False, help='input raw logs')
    parser.add_argument("--out_fpath", type=str, required=False, help='output raw logs')
    parser.add_argument("--system_os", type=str, required=False, default="linux", help="either windows or linux dataset")

    args = parser.parse_args()

    keyremoved_logs = remove_keys(args.input_fpath, args.system_os)
    if args.out_fpath:
        write_logs(keyremoved_logs, args.out_fpath)