import re
from dateutil import parser as date_parser
import datetime

def get_edgelog_timestamps(fpath, stidx, enidx):
    with open(fpath, 'r') as f:
        for i, line in enumerate(f):
            if i==stidx:
                found = re.search(r"\((.*?)\)", line)
                line_ts = date_parser.isoparse(found.group(1))
                st_timestamp = float(line_ts.timestamp())
            if i==enidx:
                found = re.search(r"\((.*?)\)", line)
                line_ts = date_parser.isoparse(found.group(1))
                en_timestamp = float(line_ts.timestamp())
    return st_timestamp, en_timestamp

def windowsts_to_unixts(windows_ts):
    return date_parser.isoparse(windows_ts).timestamp()

def unixts_to_windowsts(unix_ts):
    return datetime.datetime.fromtimestamp(unix_ts, datetime.timezone(datetime.timedelta(hours=-4))).isoformat(timespec='milliseconds')
