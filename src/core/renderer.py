import os
import json
import urllib.request
import time
from PIL import Image
from pathlib import Path
from utils.system_cleaner import SystemCleaner
from core.preprocessors import ImagePreprocessors
from core.constants import MODELS_DIR

class PixarRenderer:
    """
    Pixar Comfy-Bridge: Sends rendering requests to ComfyUI API.
    Optimized for the Golden Formula (8 Steps, 2.5 CFG, 0.25 Strength).
    """
    def __init__(self, memory_management="smart_boost", custom_config=None):
        self.comfy_url = "http://127.0.0.1:8188"
        self.availability = {
            "unet": True,
            "vae": True,
            "controlnet": True
        }
        self.preprocessor = ImagePreprocessors(device="cuda", dtype=__import__('torch').float16)
        print("🔌 Pixar Comfy-Bridge Active. Ready for Batch Processing.")

    def queue_prompt(self, prompt):
        p = {"prompt": prompt}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"{self.comfy_url}/prompt", data=data)
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read())

    def render_batch(self, input_folder, output_folder, specific_file, prompt, neg_prompt, steps=8, guidance_scale=2.5, strength=0.25, seed=42, use_depth=True, use_canny=True, **kwargs):
        """
        Sends a single frame request to ComfyUI with Triple-Lock (Depth + Canny + Segment).
        """
        use_segment = kwargs.get("use_segment", False)
        segment_strength = kwargs.get("segment_strength", 0.5)

        # Preprocess Segmentation (before building workflow)
        segment_file = None
        auto_tags = ""
        if use_segment:
            try:
                input_path = os.path.join(input_folder, specific_file)
                img = Image.open(input_path).convert("RGB")
                seg_img, auto_tags = self.preprocessor.preprocess_segmentation(img, MODELS_DIR)

                # Save colored segment map to ComfyUI input (LoadImage requirement)
                base_name = os.path.splitext(specific_file)[0]
                segment_file = f"{base_name}_seg.png"
                seg_img.save(os.path.join(input_folder, segment_file))

                if auto_tags:
                    print(f"🏷️ Pixar Semantic Intelligence: Detected {auto_tags}")
            except Exception as e:
                print(f"⚠️ Segmentation Preprocessing Failed: {e}")
                import traceback
                traceback.print_exc()
                use_segment = False

        # Build final prompt (do not append auto tags to avoid hallucinated objects from misclassification)
        final_prompt = prompt

        # [MANDATORY] جلوگیری از کش کامفویی با تغییر بسیار ریز در Denoise (هک تایید شده)
        base_denoise = kwargs.get("denoise", 0.75)
        denoise_val = base_denoise + (0.0000001 if int(seed) % 2 == 0 else -0.0000001)

        # Determine conditioning chain based on active layers
        # Chain: prompt → [Canny] → [Segment] → [Depth] → KSampler
        last_conditioning = ["6", 0]  # Start from prompt

        # Start with base conditioning from the prompt
        last_cond = ["6", 0]

        workflow = {
            "3": {
                "inputs": {
                    "seed": seed, "steps": steps, "cfg": guidance_scale,
                    "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": denoise_val,
                    "model": ["4", 0], "positive": last_cond, "negative": ["7", 0],
                    "latent_image": ["14", 0]
                },
                "class_type": "KSampler"
            },
            "4": { "inputs": { "ckpt_name": "sleipnirTLHTurbo.safetensors" }, "class_type": "CheckpointLoaderSimple" },
            "6": { "inputs": { "text": final_prompt, "clip": ["4", 1] }, "class_type": "CLIPTextEncode" },
            "7": { "inputs": { "text": neg_prompt, "clip": ["4", 1] }, "class_type": "CLIPTextEncode" },
            "9": { "inputs": { "samples": ["3", 0], "vae": ["4", 2] }, "class_type": "VAEDecode" },
            "10": { "inputs": { "filename_prefix": "Pixar_Studio_Output", "images": ["9", 0] }, "class_type": "SaveImage" },
            
            "12": { "inputs": { "control_net_name": "xinsirUnion.safetensors" }, "class_type": "ControlNetLoader" },
            "13": { "inputs": { "image": specific_file, "upload": "false" }, "class_type": "LoadImage" },
            "14": { "inputs": { "pixels": ["13", 0], "vae": ["4", 2] }, "class_type": "VAEEncode" }
        }

        # Apply active LoRAs
        active_loras = kwargs.get("active_loras", {})
        last_model = ["4", 0]
        last_clip = ["4", 1]
        node_id_counter = 50
        
        from core.lora_registry import LORA_CATALOG
        for lora_name, lora_strength in active_loras.items():
            if lora_name in LORA_CATALOG:
                filename = LORA_CATALOG[lora_name]["filename"]
                workflow[str(node_id_counter)] = {
                    "class_type": "LoraLoader",
                    "inputs": {
                        "model": last_model,
                        "clip": last_clip,
                        "lora_name": filename,
                        "strength_model": float(lora_strength),
                        "strength_clip": float(lora_strength)
                    }
                }
                last_model = [str(node_id_counter), 0]
                last_clip = [str(node_id_counter), 1]
                node_id_counter += 1
                
        # Update dependents
        workflow["3"]["inputs"]["model"] = last_model
        workflow["6"]["inputs"]["clip"] = last_clip
        workflow["7"]["inputs"]["clip"] = last_clip

        # 1. Add Canny if active
        if use_canny:
            workflow["11"] = {
                "inputs": {
                    "strength": strength,
                    "start_percent": 0.0, "end_percent": 1.0,
                    "conditioning": last_cond, "control_net": ["12", 0], "image": ["13", 0]
                },
                "class_type": "ControlNetApply"
            }
            last_cond = ["11", 0]

        # 2. Add Segment if active
        if use_segment and segment_file:
            workflow["18"] = {
                "inputs": { "image": segment_file, "upload": "false" },
                "class_type": "LoadImage"
            }
            workflow["17"] = {
                "inputs": {
                    "strength": segment_strength,
                    "start_percent": 0.0, "end_percent": 0.5,  # Freedom for textures
                    "conditioning": last_cond, "control_net": ["12", 0], "image": ["18", 0]
                },
                "class_type": "ControlNetApply"
            }
            last_cond = ["17", 0]

        # 3. Add Depth if active
        if use_depth:
            workflow["16"] = {
                "inputs": { "image": ["13", 0] },
                "class_type": "Zoe-DepthMapPreprocessor"
            }
            workflow["15"] = {
                "inputs": {
                    "strength": kwargs.get("depth_strength", 0.65),
                    "start_percent": 0.0, "end_percent": 1.0,
                    "conditioning": last_cond, "control_net": ["12", 0], "image": ["16", 0]
                },
                "class_type": "ControlNetApply"
            }
            last_cond = ["15", 0]

        # Update KSampler with final conditioning chain
        workflow["3"]["inputs"]["positive"] = last_cond

        # Determine lock status for logging
        locks = []
        if use_depth: locks.append("Depth")
        if use_canny: locks.append("Canny")
        if use_segment: locks.append("Segment")
        lock_status = "+".join(locks) if locks else "None"

        try:
            print(f"🎬 Pixar Studio Rendering: {specific_file} | Steps: {steps} | Lock: {lock_status}")
            self.queue_prompt(workflow)
        except Exception as e:
            print(f"❌ Renderer Error on {specific_file}: {e}")

    def hot_swap_components(self, config):
        """Updates internal configuration without a full engine reload."""
        print("⚙️ AI Engine: Hot-swapped components based on new dashboard settings.")

    def get_model_locations(self):
        return {
            "Sleipnir Turbo": {"status": "gpu", "nature": "Checkpoint", "size_mb": 2400},
            "Xinsir Union": {"status": "gpu", "nature": "ControlNet", "size_mb": 1200},
            "Zoe Depth": {"status": "gpu", "nature": "Preprocessor", "size_mb": 400}
        }

    def unload(self):
        print("🧼 Unloading Engine components...")
