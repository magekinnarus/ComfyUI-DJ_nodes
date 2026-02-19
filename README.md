# ComfyUI-DJ_nodes

A collection of custom nodes for ComfyUI designed to streamline workflows, specifically for SDXL, quantized models, and prompt management.

## Features

- **DJ V Prediction Param**: Force v-prediction or epsilon parameterization on models missing metadata (common in quantized models).
- **DJ Load SDXL CLIPs**: Load bundled CLIP-L and CLIP-G safetensors with automatic key normalization.
- **DJ Prompt Presets**: Manage and apply prompt presets from a JSON file with support for dynamic concatenation.

---

## Nodes Detail

### 1. DJ V Prediction Param
This node allows you to manually set the parameterization of a model. This is especially useful for **quantized models** (like GGUF) that may lack the necessary metadata for ComfyUI to automatically identify them as `v-prediction` models.

**How to use:**
1. Connect the `MODEL` output from your loader to the `model` input of this node.
2. Select either `epsilon` or `v_prediction` from the dropdown.
3. Use the `MODEL` output for your sampler.

![Workflow Screenshot](images/Workflow01.png)

---

### 2. DJ Load SDXL CLIPs
Specifically designed for loading extracted SDXL CLIP models bundled into a single safetensors file.

**Key Features:**
- Automatically handles `CLIP-L` and `CLIP-G` separation.
- Fixes common key mismatches (e.g., `conditioner.embedders`, `transformer.` prefixes).
- Injects dummy weights for missing layers (like `text_projection`) to ensure compatibility with standard loaders.
- Eliminates "missing layer" errors when loading standalone CLIP files in ComfyUI.

---

### 3. DJ Prompt Presets
A specialized prompting node that lets you quickly apply pre-defined styles or prompt blocks.

**Key Features:**
- **4 Preset Slots**: Select up to 4 different presets from `Prompt_presets/base_preset.json`.
- **Dynamic Concatenation**: Prompts and negative prompts from selected presets are automatically combined.
- **Optional Manual Input**: Includes multiline text fields for adding custom positive/negative strings to the preset sequence.
- **UI Feedback**: Displays the final concatenated positive and negative prompt strings directly on the node in ComfyUI.

**Configuration:**
Presets are stored in `Prompt_presets/base_preset.json`. You can easily add your own presets by following the JSON structure in that file.

---

## Installation

1. Navigate to the `custom_nodes` folder inside your ComfyUI directory:
   ```bash
   cd ComfyUI/custom_nodes
   ```
2. Clone this repository:
   ```bash
   git clone https://github.com/magekinnarus/ComfyUI-DJ_nodes.git
   ```
3. Restart ComfyUI.

---

## Acknowledgement
- **ComfyUI**: This suite of nodes utilizes the robust modules provided by the ComfyUI codebase.
