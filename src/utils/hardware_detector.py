\
\
\
\
   

import subprocess
import re
import psutil


class HardwareInfo:
                                                                  

    def __init__(self):
        self.total_ram_mb: int = 0                              
        self.total_vram_mb: int = 0                                     
        self.shared_vram_mb: int = 0                                     
        self.gpu_name: str = "Unknown GPU"           
        self.has_dedicated_vram: bool = False                          
        self.has_shared_memory: bool = False                                        
        self.cuda_available: bool = False                           
        self.backend: str = "cpu"                                           
        self.detection_method: str = "unknown"            

    def __repr__(self):
        return (
            f"GPU: {self.gpu_name} | "
            f"VRAM: {self.total_vram_mb} MB | "
            f"Shared: {self.has_shared_memory} ({self.shared_vram_mb} MB) | "
            f"Backend: {self.backend} | "
            f"Method: {self.detection_method}"
        )


class HardwareDetector:
\
\
\
       

                                                 
    INTEGRATED_KEYWORDS = [
        "intel", "uhd graphics", "iris", "iris xe",
        "radeon vega", "radeon graphics",           
        "adreno",                                     
        "apple m",                                         
    ]

    @classmethod
    def detect(cls) -> HardwareInfo:
        info = HardwareInfo()

                                   
        info.total_ram_mb = psutil.virtual_memory().total // (1024 ** 2)
                                                          
        info.shared_vram_mb = info.total_ram_mb // 2

                                                       
        if cls._try_torch_cuda(info):
            cls._finalize(info)
            return info

                                                   
        if cls._try_pynvml(info):
            cls._finalize(info)
            return info

                                    
        if cls._try_nvidia_smi(info):
            cls._finalize(info)
            return info

                                                         
        if cls._try_wmic(info):
            cls._finalize(info)
            return info

                                                                         
        info.gpu_name = "Unknown GPU (No Detection)"
        info.has_shared_memory = True
        info.total_vram_mb = info.total_ram_mb // 2
        info.backend = "cpu"
        info.detection_method = "fallback"
        cls._finalize(info)
        return info

                                                                               
                         
                                                                               

    @staticmethod
    def _try_torch_cuda(info: HardwareInfo) -> bool:
        try:
            import torch
            if not torch.cuda.is_available():
                return False
            props = torch.cuda.get_device_properties(0)
            info.total_vram_mb = props.total_memory // (1024 ** 2)
            info.gpu_name = props.name
            info.has_dedicated_vram = True
            info.cuda_available = True
            info.backend = "cuda"
            info.detection_method = "torch.cuda"
            return True
        except Exception:
            return False

    @staticmethod
    def _try_pynvml(info: HardwareInfo) -> bool:
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            raw_name = pynvml.nvmlDeviceGetName(handle)
            info.gpu_name = raw_name.decode() if isinstance(raw_name, bytes) else raw_name
            info.total_vram_mb = mem.total // (1024 ** 2)
            info.has_dedicated_vram = True
            info.backend = "cpu"
            info.detection_method = "pynvml"
            return True
        except Exception:
            return False

    @staticmethod
    def _try_nvidia_smi(info: HardwareInfo) -> bool:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return False
            line = result.stdout.strip().split("\n")[0]
            name, mem = line.split(",")
            info.gpu_name = name.strip()
            info.total_vram_mb = int(mem.strip())
            info.has_dedicated_vram = True
            info.backend = "cpu"
            info.detection_method = "nvidia-smi"
            return True
        except Exception:
            return False

    @classmethod
    def _try_wmic(cls, info: HardwareInfo) -> bool:
\
\
\
           
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController",
                 "get", "Name,AdapterRAM,VideoMemoryType",
                 "/format:list"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return False

            blocks = result.stdout.strip().split("\n\n")
            best = None                            

            for block in blocks:
                parsed = {}
                for line in block.strip().split("\n"):
                    if "=" in line:
                        key, _, val = line.partition("=")
                        parsed[key.strip()] = val.strip()

                name = parsed.get("Name", "").strip()
                if not name:
                    continue

                adapter_ram_str = parsed.get("AdapterRAM", "0").strip()
                try:
                    adapter_ram_mb = int(adapter_ram_str) // (1024 ** 2)
                except ValueError:
                    adapter_ram_mb = 0

                                                                    
                is_integrated = any(
                    kw in name.lower() for kw in cls.INTEGRATED_KEYWORDS
                )
                if best is None or (not is_integrated and best["integrated"]):
                    best = {
                        "name": name,
                        "adapter_ram_mb": adapter_ram_mb,
                        "integrated": is_integrated
                    }

            if best is None:
                return False

            info.gpu_name = best["name"]
            info.has_shared_memory = best["integrated"]
            info.has_dedicated_vram = not best["integrated"]

            if best["integrated"]:
                                                                                
                                                            
                info.total_vram_mb = min(
                    best["adapter_ram_mb"] if best["adapter_ram_mb"] > 512 else info.total_ram_mb // 2,
                    info.total_ram_mb // 2
                )
            else:
                info.total_vram_mb = best["adapter_ram_mb"]

            info.backend = "cpu"
            info.detection_method = "wmic"
            return True

        except Exception:
            return False

    @classmethod
    def _finalize(cls, info: HardwareInfo):
\
\
\
\
           
        gpu_lower = info.gpu_name.lower()

        if not info.has_shared_memory:
                                                                                           
            if any(kw in gpu_lower for kw in cls.INTEGRATED_KEYWORDS) or info.shared_vram_mb > 0:
                info.has_shared_memory = True
                if any(kw in gpu_lower for kw in cls.INTEGRATED_KEYWORDS):
                    info.has_dedicated_vram = False
                    if info.total_vram_mb > info.total_ram_mb // 2:
                        info.total_vram_mb = info.total_ram_mb // 2

                                     
        if info.total_vram_mb <= 0:
            if info.has_shared_memory:
                info.total_vram_mb = info.total_ram_mb // 2
            else:
                info.total_vram_mb = 4096                    

    @staticmethod
    def get_vram_usage():
                                                                  
        try:
            import torch
            if torch.cuda.is_available():
                                                                         
                used = torch.cuda.memory_reserved(0) // (1024**2)
                return used
        except: pass
        
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return info.used // (1024**2)
        except: return 0

    @staticmethod
    def get_gpu_load():
                                           
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temp = pynvml.nvmlDeviceGetTemperature(handle, 0)
            return util.gpu, temp
        except: return 0, 0
