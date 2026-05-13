import psutil
try:
    from py3nvml import py3nvml
    py3nvml.nvmlInit()
    HAS_GPU = True
except:
    HAS_GPU = False

class ResourceMonitor:
    _gpu_handle = None

    @classmethod
    def _get_handle(cls):
        if cls._gpu_handle is None and HAS_GPU:
            try:
                cls._gpu_handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
            except:
                pass
        return cls._gpu_handle

    @classmethod
    def get_gpu_info(cls):
        if not HAS_GPU: return None
        handle = cls._get_handle()
        if not handle: return None
        
        try:
                                                                  
            try: mem = py3nvml.nvmlDeviceGetMemoryInfo(handle)
            except: mem = None
            
            try: temp = py3nvml.nvmlDeviceGetTemperature(handle, py3nvml.NVML_TEMPERATURE_GPU)
            except: temp = 0
            
            try: util = py3nvml.nvmlDeviceGetUtilizationRates(handle)
            except: util = None
            
            if mem:
                return {
                    "vram_perc": mem.used / mem.total,
                    "vram_used": mem.used // 1024**2,
                    "vram_total": mem.total // 1024**2,
                    "temp": temp,
                    "load": util.gpu if util else 0
                }
        except Exception as e:
            print(f"Monitor GPU Error: {e}")
            return None
        return None

    @staticmethod
    def get_cpu_info():
        try:
            load = psutil.cpu_percent()
            cpu_temp = 0
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if "coretemp" in temps: cpu_temp = temps["coretemp"][0].current
                elif "cpu_thermal" in temps: cpu_temp = temps["cpu_thermal"][0].current
            
            return {"load": load, "temp": cpu_temp}
        except: return {"load": 0, "temp": 0}

    @staticmethod
    def get_color(perc):
        if perc < 0.5: return "#2ecc71"        
        if perc < 0.8: return "#f1c40f"         
        return "#e74c3c"      

    @staticmethod
    def shutdown():
        if HAS_GPU:
            try: py3nvml.nvmlShutdown()
            except: pass
