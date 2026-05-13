import torch
import gc

class SystemCleaner:
    @staticmethod
    def deep_purge():
        """Aggressively clears system RAM and GPU VRAM."""
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        return True

    @staticmethod
    def clean_ghosts():
        """Aggressively identifies and kills orphan Python processes running Pixar scripts."""
        import os
        import psutil
        
        current_pid = os.getpid()
        killed_count = 0
        
        print(f"🧹 Scanning for ghost processes... (Current PID: {current_pid})")
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Target python processes
                name = proc.info['name'] or ""
                if 'python' in name.lower():
                    pid = proc.info['pid']
                    if pid == current_pid:
                        continue
                        
                    cmdline = proc.info['cmdline']
                    # Check if it's a Pixar related process (path or script name)
                    if cmdline and any('Pixar' in part for part in cmdline):
                        print(f"💀 Killing ghost process: {pid} ({name})")
                        proc.kill()
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return killed_count

    @staticmethod
    def nuclear_shutdown():
        """Performs a clean but complete shutdown of all AI resources."""
        import os
        import signal
        SystemCleaner.deep_purge()
        # Note: We don't actually want to kill the parent process here unless needed
        # but we ensure GPU is clean.
