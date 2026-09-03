from enum import Enum

class InputFormat(Enum):
    edge = """The audit log data from a {os_type} system has been processed into an information-flow graph. Each line of input now represents an information flow edge that describes an action between two nodes, and each node corresponds to one of three objects: a process, file and network socket. Each input edge contains the following information:

"(timestamp of action) [unique source node ID]{{key-value pairs of source node attributes separated by commas}} --> [unique edge ID]{{key-value pairs of the action's attributes separated by commas}} --> [unique destination node ID]{{key-value pairs of destination node separated by commas}}" """

    raw = """The input audit log data of Linux system is obtained directly from Auditd framework and should be used for the identification of {task_name}."""