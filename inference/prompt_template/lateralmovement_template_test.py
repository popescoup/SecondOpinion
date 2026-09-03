from prompt_v2 import Prompt
from prompt_template.input_format import InputFormat
from prompt_template.ostype import OSType

from prompt_template.lateralmovement_template_v2 import LateralMovementPrompt

if __name__ == "__main__":

    lateral_movement_prompt = Prompt(
        task = "lateral movement",
        os_type = OSType.windows,
        goal = LateralMovementPrompt.GOAL,
        output_description = LateralMovementPrompt.OUTPUT_DESCRIPTION,
        json_output_format = LateralMovementPrompt.OUTPUT_FORMAT,
        log_input_format = InputFormat.edge
    )
    print(lateral_movement_prompt.populate("toy log data"))