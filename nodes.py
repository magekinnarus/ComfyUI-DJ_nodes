import torch
import comfy.sd
import comfy.utils
import folder_paths

class SDXLCliploader:
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

class AddParam:
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

# Ensure both nodes are registered for ComfyUI
NODE_CLASS_MAPPINGS = {
    "AddParam": AddParam,
    "SDXLCliploader": SDXLCliploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AddParam": "Add Model Parameterization",
    "SDXLCliploader": "Load Extracted SDXL CLIP"
}