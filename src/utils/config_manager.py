import json
import os
from utils.schema import PixarSchema

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "mem": PixarSchema.MEMORY_MODES[0],
            "seed": PixarSchema.DEFAULTS["seed"],
            "steps": PixarSchema.DEFAULTS["steps"],
            "denoise": PixarSchema.DEFAULTS["denoise"],
            "cfg": PixarSchema.DEFAULTS["cfg"],
            "guidance_scale": PixarSchema.DEFAULTS["cfg"],
            "input": PixarSchema.DEFAULTS["input"],
            "output": PixarSchema.DEFAULTS["output"],
            "ref_strength": PixarSchema.DEFAULTS["ref_strength"],
            "depth_strength": PixarSchema.DEFAULTS["depth_strength"],
            "strength": PixarSchema.DEFAULTS["strength"],
            "expert_prompt": PixarSchema.DEFAULTS["expert_prompt"],
            "negative_prompt": "8-bit, 16-bit, low-poly, simple textures, flat lighting, amateur render, grainy, blurry, low resolution, distorted geometry, plastic look, floating pixels, artificial grid",
            "lang": "fa",
            "use_depth": PixarSchema.DEFAULTS["use_depth"],
            "use_canny": PixarSchema.DEFAULTS["use_canny"],
            "use_ip_adapter": PixarSchema.DEFAULTS["use_ip_adapter"],
            "canny_low": 100,
            "canny_high": 200,
            "auto_canny": False,
            "random_seed": False
        }

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                                                                                      
                    for key, val in self.default_config.items():
                        if key not in data or data[key] is None:
                            print(f"⚠️ Config: Field '{key}' was missing/null — reset to default.")
                            data[key] = val
                    return data
            except Exception as e:
                print(f"⚠️ Config load failed ({e}) — using defaults.")
        return self.default_config

    def save(self, config_data):
\
\
           
        import tempfile
        import threading
        
                                                
        if not hasattr(self, "_lock"):
            self._lock = threading.Lock()
            
        with self._lock:
            temp_dir = os.path.dirname(os.path.abspath(self.config_file))
            fd, temp_path = tempfile.mkstemp(dir=temp_dir, prefix="config_", suffix=".tmp")
            try:
                with os.fdopen(fd, 'w') as f:
                    json.dump(config_data, f, indent=4)
                
                                              
                                                                                                 
                os.replace(temp_path, self.config_file)
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"⚠️ Config Save Error: {e}")
