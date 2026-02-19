import torch
import comfy.sd
import comfy.utils
import folder_paths
import os
import json

def get_presets():
    presets_path = os.path.join(os.path.dirname(__file__), "Prompt_presets", "base_preset.json")
    if not os.path.exists(presets_path):
        return {}
    try:
        with open(presets_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["name"]: item for item in data}
    except Exception as e:
        print(f"Error loading presets: {e}")
        return {}

class DJ_cliploader:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"clip_name": (folder_paths.get_filename_list("clip"), )}}
    
    RETURN_TYPES = ("CLIP",)
    FUNCTION = "load_dual_clip"
    CATEGORY = "custom_loaders"

    def load_dual_clip(self, clip_name):
        clip_path = folder_paths.get_full_path("clip", clip_name)
        sd = comfy.utils.load_torch_file(clip_path)

        # DEBUG: Print keys to console to diagnose mismatches
        print(f"DEBUG: Total keys in file: {len(sd)}")
        if len(sd) > 0:
            print(f"DEBUG: First 5 keys: {list(sd.keys())[:5]}")

        # 1. SPLIT BY PREFIX: Identify CLIP-L vs CLIP-G
        sd_l = {}
        sd_g = {}
        for k, v in sd.items():
            # CLIP-L Logic
            if "conditioner.embedders.1" in k:
                # Standard SDXL checkpoint format
                if "conditioner.embedders.1.model." in k:
                    new_k = k.replace("conditioner.embedders.1.model.", "")
                else:
                    new_k = k.replace("conditioner.embedders.1.", "")
                
                # Fix for OpenCLIP format missing 'transformer.' prefix for blocks
                if new_k.startswith("resblocks."):
                    new_k = "transformer." + new_k
                
                sd_l[new_k] = v
            elif "clip_l." in k:
                # Extracted with simple prefixes
                new_k = k.replace("clip_l.", "")
                if new_k.startswith("resblocks."):
                    new_k = "transformer." + new_k
                sd_l[new_k] = v
            
            # CLIP-G Logic
            elif "conditioner.embedders.0" in k:
                # Standard SDXL checkpoint format
                if "conditioner.embedders.0.model." in k:
                    new_k = k.replace("conditioner.embedders.0.model.", "")
                else:
                    new_k = k.replace("conditioner.embedders.0.", "")
                
                # Fix for CLIP-G having extra 'transformer.' prefix
                if new_k.startswith("transformer."):
                    new_k = new_k.replace("transformer.", "")
                    
                sd_g[new_k] = v
            elif "clip_g." in k:
                # Extracted with simple prefixes
                new_k = k.replace("clip_g.", "")
                if new_k.startswith("transformer."):
                    new_k = new_k.replace("transformer.", "")
                sd_g[new_k] = v

        print(f"DEBUG: keys in sd_l: {len(sd_l)}")
        if len(sd_l) > 0: print(f"DEBUG: sd_l sample: {list(sd_l.keys())[:3]}")
        print(f"DEBUG: keys in sd_g: {len(sd_g)}")
        if len(sd_g) > 0: print(f"DEBUG: sd_g sample: {list(sd_g.keys())[:3]}")

        # 2. INJECT MISSING KEYS FOR CLIP-L (Bypass strict check)
        # CLIP-L (sd_l) typically lacks these keys, but generic loading might expect them
        # Only inject if we actually have a CLIP-L (sd_l is not empty)
        if len(sd_l) > 0:
            if "text_projection.weight" not in sd_l and "text_projection" not in sd_l:
                sd_l["text_projection.weight"] = torch.eye(768, dtype=torch.float32)
            if "logit_scale" not in sd_l:
                sd_l["logit_scale"] = torch.tensor(4.6055, dtype=torch.float32)

        # 3. LOAD USING CORRECT API
        # We pass both dictionaries; ComfyUI will detect TEModel.CLIP_L and TEModel.CLIP_G
        # and construct an SDXLClipModel or appropriate equivalent.
        clip = comfy.sd.load_text_encoder_state_dicts(
            [sd_l, sd_g],
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
            clip_type=comfy.sd.CLIPType.STABLE_DIFFUSION
        )
        
        return (clip,)

class DJ_V_Prediction:
    parameterization_options = ["epsilon", "v_prediction"]  # Both options in the dropdown

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "parameterization": (s.parameterization_options,),  # Required input
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "add_parameterization"

    CATEGORY = "advanced/model"

    def add_parameterization(self, model, parameterization):
        m = model.clone()

        if parameterization == "v_prediction":
            internal_parameterization = "v"  # Set internal value to "v"
            setattr(m.model, "parameterization", internal_parameterization)
            from comfy.model_sampling import V_PREDICTION, ModelSamplingDiscrete
            class ModelSamplingAdvanced(ModelSamplingDiscrete, V_PREDICTION):
                pass
            m.add_object_patch("model_sampling", ModelSamplingAdvanced(m.model.model_config))
        # No 'elif' for epsilon - this is the key for the bypass

        return (m,)  # Return the (potentially modified) model

class DJ_PromptPresets:
    @classmethod
    @classmethod
    def INPUT_TYPES(s):
        presets = get_presets()
        preset_names = ["None"] + list(presets.keys())
        return {
            "required": {
                "clip": ("CLIP",),
                "preset_1": (preset_names,),
                "preset_2": (preset_names,),
                "preset_3": (preset_names,),
                "preset_4": (preset_names,),
            },
            "optional": {
                "generated_positive": ("STRING", {"multiline": True, "default": "", "forceInput": False}),
                "generated_negative": ("STRING", {"multiline": True, "default": "", "forceInput": False}),
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "STRING", "STRING")
    RETURN_NAMES = ("POSITIVE", "NEGATIVE", "pos_text", "neg_text")
    FUNCTION = "apply_presets"
    CATEGORY = "DJ_nodes/Prompting"

    def apply_presets(self, clip, preset_1, preset_2, preset_3, preset_4, generated_positive="", generated_negative=""):
        presets = get_presets()
        selected_presets = [preset_1, preset_2, preset_3, preset_4]
        
        final_pos_str = ""
        final_neg_str = ""

        # Concatenate strings first
        for p_name in selected_presets:
            if p_name == "None" or p_name not in presets:
                continue
            
            p_data = presets[p_name]
            p_pos = p_data.get("prompt", "").strip()
            p_neg = p_data.get("negative_prompt", "").strip()
            
            if p_pos:
                final_pos_str = (final_pos_str + ", " + p_pos) if final_pos_str else p_pos
            if p_neg:
                final_neg_str = (final_neg_str + ", " + p_neg) if final_neg_str else p_neg

        def encode_text(text, clip):
            tokens = clip.tokenize(text)
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            return [[cond, {"pooled_output": pooled}]]

        # Encode once
        pos_cond = encode_text(final_pos_str, clip)
        neg_cond = encode_text(final_neg_str, clip)

        return {
            "ui": {
                "generated_positive": [final_pos_str],
                "generated_negative": [final_neg_str]
            },
            "result": (pos_cond, neg_cond, final_pos_str, final_neg_str)
        }

# Ensure nodes are registered for ComfyUI
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