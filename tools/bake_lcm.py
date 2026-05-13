import torch
from diffusers import StableDiffusionXLPipeline
import os

def bake_lcm():
    model_id = "C:/Users/ATekno_Merve/Desktop/alireza/Pixar/models/solid_models/Juggernaut-XL"
    lcm_lora_id = "latent-consistency/lcm-lora-sdxl"
    new_path = "C:/Users/ATekno_Merve/Desktop/alireza/Pixar/models/solid_models/Juggernaut-LCM-XL"

    print("🚀 Loading base Juggernaut XL pipeline onto CPU...")
                                                       
    pipe = StableDiffusionXLPipeline.from_pretrained(
        model_id, 
        torch_dtype=torch.float16,
        use_safetensors=True,
        local_files_only=True
    ).to("cpu")

    print(f"📥 Downloading and Loading LCM-LoRA from '{lcm_lora_id}'...")
    try:
        pipe.load_lora_weights(lcm_lora_id)
    except Exception as e:
        print(f"❌ Error downloading/loading LoRA: {e}")
        print("Please ensure your internet connection allows HuggingFace access.")
        return

    print("🔥 Fusing LoRA weights into UNet...")
    pipe.fuse_lora()
    
    print("🧹 Unloading separate LoRA weights to clean up...")
    pipe.unload_lora_weights()

    print(f"💾 Saving new fused pipeline to '{new_path}'...")
    os.makedirs(new_path, exist_ok=True)
    pipe.save_pretrained(new_path, safe_serialization=True)
    
    print("✅ Baking complete! The new model is ready.")

if __name__ == "__main__":
    bake_lcm()
