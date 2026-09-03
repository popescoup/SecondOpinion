from prompt_v2 import Prompt
from prompt_template.input_format import InputFormat
from prompt_template.ostype import OSType

from prompt_template.persistence_template_v2 import PersistencePrompt

if __name__ == "__main__":

    persistence_prompt = Prompt(
        task = "persistence",
        os_type = OSType.windows,
        output_description = PersistencePrompt.OUTPUT_DESCRIPTION,
        goal = PersistencePrompt.GOAL,
        json_output_format = PersistencePrompt.OUTPUT_FORMAT,
        log_input_format = InputFormat.edge,
        additional_sections=PersistencePrompt.ADDITIONAL_SECTION,
        mitre_output=PersistencePrompt.OUTPUT_FORMAT_MITRE,
    )
    print(persistence_prompt.populate("toy log data"))