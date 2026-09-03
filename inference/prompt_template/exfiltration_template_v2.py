
class ExfiltrationPrompt():

    GOAL = """You are tasked with identifying exfiltration activty by a potential attacker, that is, actions that cause user-generated data to leave the system. Look for activities such as external drive shares, USB activity, uploads to websites like Dropbox, iCloud, etc., outgoing data transfer over various protocols like HTTPS, or other types of exfiltration. The user-generated data consist of files and directories that are created by the users of system and the attacker may compress or encrypt them before exfiltration.
    
Do not report the data that are not user-generated, e.g. system-generated files or temporary files.

You must identify all exfiltration actions that may be used by potential attacker to steal the user-generated data, and assess how suspicious each action is, i.e., likely to be caused by an attacker."""

    OUTPUT_DESCRIPTION = """For each relevant action in the logs that indicates suspicious data exfiltration behavior, return a JSON object following the format specified below."""

    OUTPUT_FORMAT = [
        ("key log lines", "str", "list of comma separated log lines showing {task} of all the user-generated data involved in the data {task} activity"),
        ("timestamp", "str", "timestamp of the {task} action."),
        ("pid", "int", "the PID of the process performing the data {task} action."),
        ("exfiltration method", "str", "if the user-generated data was exfiltrated, how was it exfiltrated?"),
        ("exfiltrated data", "str", "the full file path of the user-generated files that are exfiltrated. To generate the full file path, combine the directory path and file name."),
        ("evidence for", "str", "describe all the evidence from the key log lines that indicates suspicious data {task}."),
        ("evidence against", "str", "describe all the evidence from the key log lines that indicates either not suspicious or not data {task}."),
        ("deliberation", "str", "analyze the evidence above, taking into account evidence for and against, in order to reach a conclusion."),
        ("verdict", "str", "one of ['LOW_SUSPICIOUS', 'MEDIUM_SUSPICIOUS', 'HIGH_SUSPICIOUS']. Use 'HIGH_SUSPICIOUS' only when the identified behavior is highly likely for an attacker to create malicious {task}. Use 'MEDIUM_SUSPICIOUS' when it is not clear how feasible it would be for an attacker to abuse. Use 'LOW_SUSPICIOUS' when the activity is likely benign, part of regular system activity, or generally difficult for the attacker to use as {task}."),
    ]
