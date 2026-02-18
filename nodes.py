import torch
import comfy.model_management
import comfy.model_sampling
import comfy.sd # Added for checkpoint guessing logic
import folder_paths # Added to find files in model directories

class SDXLCliploader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip_name": (folder_paths.get_filename_list("clip"), {"tooltip": "The combined extracted CLIP safetensors file."}),
            }
        }
    
    RETURN_TYPES = ("CLIP",)
    FUNCTION = "load_clip"
    CATEGORY = "loaders"

    def load_clip(self, clip_name):
        # Locate the path in the 'clip' directory
        clip_path = folder_paths.get_full_path_or_raise("clip", clip_name)
        
        # We reuse the internal checkpoint guessing logic used by CheckpointLoaderSimple.
        # By setting output_model and output_vae to False, we avoid looking for 
        # UNet/VAE tensors and trigger the path that allows missing layers like logit_scale.
        out = comfy.sd.load_checkpoint_guess_config(
            clip_path, 
            output_vae=False, 
            output_clip=True, 
            output_model=False, 
            embedding_directory=folder_paths.get_folder_paths("embeddings")
        )
        
        # Returns index 1 of the tuple, which is the initialized CLIP object
        return (out[1],)

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