# Classes are defined in nodes.py rather than separate modules.
from .nodes import AddParam, SDXLCliploader

NODE_CLASS_MAPPINGS = {
    "AddParam": AddParam,
    "SDXLCliploader": SDXLCliploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AddParam": "Add Model Parameterization",
    "SDXLCliploader": "Load Extracted SDXL CLIP"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']