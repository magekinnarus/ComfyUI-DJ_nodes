# Classes are defined in nodes.py rather than separate modules.
from .nodes import DJ_V_Prediction, DJ_cliploader, DJ_PromptPresets

NODE_CLASS_MAPPINGS = {
    "DJ_V_Prediction": DJ_V_Prediction,
    "DJ_cliploader": DJ_cliploader,
    "DJ_PromptPresets": DJ_PromptPresets
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DJ_V_Prediction": "DJ V Prediction Param",
    "DJ_cliploader": "DJ Load SDXL CLIPs",
    "DJ_PromptPresets": "DJ Prompt Presets"
}

WEB_DIRECTORY = "./js"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']