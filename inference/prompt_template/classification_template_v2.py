
class ClassificationPrompt():

    GOAL = """You are tasked with investigating whether a given system has been compromise by an attacker or not. If attacker activity occurred, you must also identify all specific attacker actions that took place, and assess how suspicious each action is, i.e., likely to be caused by an attacker."""

    OUTPUT_DESCRIPTION = """Return exactly one JSON object following the format specified below."""

    OUTPUT_FORMAT = [
        ("key log lines", "str", "list of comma separated log lines showing {task} activity, if any. Every log line should be on a new line."),
        ("evidence for", "str", "describe all the evidence from the key log lines that indicates {task} on system."),
        ("evidence against", "str", "describe all the evidence from the key log lines that may indicate benign activity instead."),
        ("deliberation", "str", "analyze the evidence above, taking into account evidence for and against, in order to reach a conclusion."),
        ("verdict", "str", "one of ['LOW_SUSPICIOUS', 'MEDIUM_SUSPICIOUS', 'HIGH_SUSPICIOUS']. Use 'HIGH_SUSPICIOUS' only when the identified behavior is highly likely to be malicious by an attacker. Use 'MEDIUM_SUSPICIOUS' when it is not clear how feasible it would be for an attacker to abuse. Use 'LOW_SUSPICIOUS' when the activity is likely benign, part of regular system activity, or generally difficult for the attacker to use as {task}."),
    ]