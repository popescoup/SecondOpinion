import json
import os
from prompt_template.input_format import InputFormat
from prompt_template.ostype import OSType

class Prompt:

    PERSONA = "You are a highly-skilled computer security expert with decades of experience in forensic system logs analysis."
    
    def __init__(self, task, os_type, goal, output_description, json_output_format, log_input_format, additional_sections=None, mitre_output=None):
        
        self.task = task
        self.goal = goal
        self.output_description = output_description
        self.json_output_format = json_output_format
        self.os_type = os_type
        self.log_input_format = log_input_format
        self.additional_sections = additional_sections or ""
        self.mitre_output = mitre_output
        
        if self.log_input_format == InputFormat.raw:
            assert self.os_type == OSType.linux

    def populate(self, logs: str) -> str:

        output_format = '\n'.join(f'    "{key}": {typ},  # {description}' for key, typ, description in self.json_output_format)
        output_format = output_format.format(task=self.task)
        
        if self.mitre_output:
            mitre_output_str = '\n'.join(f'    "{key}": {typ},  # {description}' for key, typ, description in self.mitre_output)
            mitre_output_str = mitre_output_str.format(task=self.task)
            mitre_output_str = "\n" + mitre_output_str
        else:
            mitre_output_str = ""
        
        if self.log_input_format == InputFormat.edge:
            input_format = self.log_input_format.value.format(os_type=self.os_type.value)
        elif self.log_input_format == InputFormat.raw:
            input_format = self.log_input_format.value.format(task_name=self.task)
        else:
            raise ValueError("Unhandled input format")
        
        if self.additional_sections:
            additional_sections_str = f"\n{self.additional_sections}\n"
        else:
            additional_sections_str = "" 

        template = f"""{self.PERSONA}

# Goal

{self.goal}

# Setup

To accomplish this task, you are given a set of {self.os_type.value} audit system logs below.

## Input log format

{input_format}

## Instructions for reporting {self.task} actions

Report your findings, if any, by using one or more JSON objects following the format specified below.

{self.output_description}

```
{{
{output_format}{mitre_output_str}
}}
```

If no potential {self.task} activity is found, return a single empty JSON object.
{additional_sections_str}
# Data

The input audit log data that should be used for the identification of {self.task} is as follows:

{logs}
"""
        return template


    def save_prompt(self, fpath, prompt_key, prompt):
        dir_name = os.path.dirname(fpath)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        if not os.path.exists(fpath):
            open(fpath, 'w').close()
        
        with open(fpath, 'r+') as f:
            for line in f:
                d = json.loads(line, strict=False)
                for k in d:
                    if k == prompt_key:
                        return
            
            newjson_line = json.dumps({prompt_key: prompt})
            f.write(newjson_line + "\n")
