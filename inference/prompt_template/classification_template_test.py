from prompt_v2 import Prompt
from prompt_template.input_format import InputFormat
from prompt_template.ostype import OSType

from prompt_template.classification_template_v2 import ClassificationPrompt

if __name__ == "__main__":

    classification_prompt = Prompt(
        task = "attack",
        os_type = OSType.windows,
        output_description = ClassificationPrompt.OUTPUT_DESCRIPTION,
        goal = ClassificationPrompt.GOAL,
        json_output_format = ClassificationPrompt.OUTPUT_FORMAT,
        log_input_format = InputFormat.edge,
    )
    print(classification_prompt.populate("toy log data"))