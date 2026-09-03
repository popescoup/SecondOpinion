from prompt_v2 import Prompt
from prompt_template.input_format import InputFormat
from prompt_template.ostype import OSType

from prompt_template.exfiltration_template_v2 import ExfiltrationPrompt

if __name__ == "__main__":

    exfiltration_prompt = Prompt(
        task = "exfiltration",
        os_type = OSType.linux,
        output_description = ExfiltrationPrompt.OUTPUT_DESCRIPTION,
        goal = ExfiltrationPrompt.GOAL,
        json_output_format = ExfiltrationPrompt.OUTPUT_FORMAT,
        log_input_format = InputFormat.edge,
    )
    print(exfiltration_prompt.populate("toy log data"))