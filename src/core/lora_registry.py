
# LoRA Catalog for Pixar AI Studio
# This registry maps LoRA models to their physical filenames and categories.

CATEGORY_COLORS = {
    "Texture": "#3498db",  # Blue
    "Lighting": "#f1c40f", # Yellow
    "Character": "#e74c3c", # Red
    "Environment": "#2ecc71", # Green
    "Style": "#9b59b6"      # Purple
}

CATEGORY_ICONS = {
    "Texture": "🧱",
    "Lighting": "💡",
    "Character": "👤",
    "Environment": "🌳",
    "Style": "🎨"
}

LORA_CATALOG = {
    "Mythic Realism": {
        "filename": "Realism_Environment.safetensors",
        "category": "Environment",
        "strength": 0.8,
        "min_strength": 0.0,
        "max_strength": 1.5,
        "description": "Photorealistic environment details and natural textures."
    },
    "God Rays": {
        "filename": "God_Rays_Volumetric.safetensors",
        "category": "Lighting",
        "strength": 0.7,
        "min_strength": 0.0,
        "max_strength": 1.5,
        "description": "Cinematic volumetric lighting and sunbeams."
    },
    "Dense Forest": {
        "filename": "Dense_Forest_Overgrowth.safetensors",
        "category": "Environment",
        "strength": 0.8,
        "min_strength": 0.0,
        "max_strength": 1.5,
        "description": "Thick vegetation, overgrowth, and lush forest canopy."
    }
}

def is_lora_installed(lora_name, models_dir=None):
    import os
    from pathlib import Path
    if lora_name not in LORA_CATALOG:
        return False
    filename = LORA_CATALOG[lora_name]["filename"]
    # ComfyUI stores loras in its own models/loras/ directory
    comfyui_lora_path = Path(__file__).resolve().parent.parent.parent / "ComfyUI" / "models" / "loras" / filename
    return comfyui_lora_path.exists()
