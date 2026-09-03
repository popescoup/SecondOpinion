
class LateralMovementPrompt():

    GOAL = """You are tasked with identifying activity that may be used as lateral movement by a potential attacker, that is, actions that can allow an adversary to move through a network.

Specifically, lateral movement consists of techniques by which a user establishes successful outgoing connections to external machines in a way that allows the user to enter and control the remote systems. Outgoing connections consist of connections initiated by the current machine, whereas incoming connections involve receiving data without first initiating the connection.

You must identify all specific actions that may be used for lateral movement, and assess how suspicious each action is, i.e., likely to be caused by an attacker."""

    OUTPUT_DESCRIPTION = """If a user makes multiple suspicious outgoing connections to an external machine using the same method, then report this activity in a single JSON object. If different users initiate suspicious outgoing connections to an external machine, report each of the outgoing connections as separate suspicious lateral movement JSON objects."""

    OUTPUT_FORMAT = [
        ("key log line", "str", "the key log line showing {task}."),
        ("timestamp", "str", "timestamp of the log record demonstrating {task}."),
        ("external host", "str", "the IP address, hostname, or identifier of the external destination machine."),
        ("pid", "int", "pid of the process used for {task}."),
        ("username", "str", "username of the user who initiated the outgoing {task} connection to the remote system."),
        ("evidence for", "str", "describe all the evidence from the key log line that indicates suspicious {task}."),
        ("evidence against", "str", "describe all the evidence from the key log line that indicates either not suspicious or not {task}."),
        ("deliberation", "str", "analyze the evidence above, taking into account evidence for and against, in order to reach a conclusion."),
        ("verdict", "str", "one of ['LOW_SUSPICIOUS', 'MEDIUM_SUSPICIOUS', 'HIGH_SUSPICIOUS']. Use 'HIGH_SUSPICIOUS' only when the identified behavior is highly likely for an attacker to use as {task}. Use 'MEDIUM_SUSPICIOUS' when it is not clear how feasible it would be for an attacker to abuse. Use 'LOW_SUSPICIOUS' when the activity is likely benign, part of regular system activity, or generally difficult for the attacker to use as {task}."),
    ]
