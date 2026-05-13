
import os
import glob

class PixarSchema:
    MODELS = {
        "TEXT_ENCODER": "Text Encoder",
        "UNET": "UNet (Main Denoising)",
        "CONTROLNET": "ControlNet (Structure)",
        "VAE": "VAE (Image Decoder)"
    }
    
    MODELS_META = {
        "Text Encoder": {"size_mb": 250},
        "UNet (Main Denoising)": {"size_mb": 4900},
        "ControlNet (Structure)": {"size_mb": 300},
        "VAE (Image Decoder)": {"size_mb": 320}
    }

    ART_STYLES = ["None (Disabled)", "organic", "clean_voxel", "realistic_nature", "papercraft"]
    LIGHTING_MOODS = ["None (Disabled)", "Golden Hour", "Cinematic Blue", "Volumetric Fog", "Cyberpunk Neon", "Midnight Glow"]
    MEMORY_MODES = ["smart_boost", "custom"]
    MEM_LEVELS = ["Auto", "King"]                   

    PROMPT_PRESETS = {}

    DEFAULTS = {
        "seed": "42",
        "steps": 8,          # Validated Golden Safe Point
        "denoise": 0.75,     # Golden Value for Pixar Magic
        "strength": 0.25,    # Structure Lock (Canny Golden Value)
        "depth_strength": 0.65, # Zoe Depth Lock (Golden Value)
        "cfg": 2.5,          # Pixar Contrast (Golden Value)
        "ref_strength": 0.50,                                   
        "input": r"c:\Users\ATekno_Merve\Desktop\alireza\Pixar\ComfyUI\input",
        "output": r"c:\Users\ATekno_Merve\Desktop\alireza\Pixar\ComfyUI\output",
        "simple_prompt": "",
        "expert_prompt": "polished high-end CGI anime form, complex hyper-realistic material layering, highly textured surfaces, masterful volumetric lighting, cinematic fog, deep atmospheric depth, professional framing, 8k resolution, ray-traced reflections, sharp focus",
        "negative_prompt": "8-bit, 16-bit, low-poly, simple textures, flat lighting, amateur render, grainy, blurry, low resolution, distorted geometry, plastic look, floating pixels, artificial grid",
        "canny_low": 100,
        "canny_high": 200,
        "auto_canny": False,
        "use_depth": True,
        "use_canny": False,
        "use_ip_adapter": False, # Disabled by default as requested (grayed out)
        "custom_vram": {
            "UNet (Main Denoising)": "King",
            "ControlNet (Structure)": "Auto",
            "VAE (Image Decoder)": "Auto",
            "Text Encoder": "Auto"
        }
    }

    @classmethod
    def get_model_list(cls):
        return list(cls.MODELS.values())

    lock_scanning = False                                    

    @classmethod
    def scan_all_physical_models(cls, models_dir):
        results = []
        all_files = []
        for ext in ["*.safetensors", "*.pt", "*.ckpt"]:
            search_path = os.path.join(models_dir, "**", ext)
            all_files.extend(glob.glob(search_path, recursive=True))

        for file_path in all_files:
            path_lower = file_path.lower().replace("\\", "/")
            
            if "/_" in path_lower:
                continue

            nature = "Unknown"

            if "/unet/" in path_lower:
                nature = "UNet (Main Denoising)"
            elif "/vae/" in path_lower:
                nature = "VAE (Image Decoder)"
            elif "/text_encoder/" in path_lower or "/text_encoder_2/" in path_lower:
                nature = "Text Encoder"
            elif "controlnet" in path_lower:
                nature = "ControlNet (Structure)"

            if nature != "Unknown":
                results.append({
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "nature": nature,
                    "size_mb": os.path.getsize(file_path) / (1024**2)
                })

        return results

    @classmethod
    def resolve_dynamic_models(cls, models_dir):
        """Resolves physical file paths for required AI models."""
        all_models = cls.scan_all_physical_models(models_dir)
        resolved = {}
        
        for key, display_name in cls.MODELS.items():
            matches = [m for m in all_models if m["nature"] == display_name]
            if matches:
                resolved[display_name] = {
                    "path": matches[0]["path"],
                    "filename": matches[0]["filename"],
                    "all_files": [m["path"] for m in matches]
                }
            else:
                resolved[display_name] = {
                    "path": None,
                    "filename": "Unknown",
                    "all_files": []
                }
        return resolved
