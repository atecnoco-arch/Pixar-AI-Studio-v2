import threading
import os
import traceback
import time
import random
from core.renderer import PixarRenderer, SystemCleaner
from core.constants import GAP_LIMIT, SUPPORTED_EXTENSIONS, FREEU_MAX_VALUES
from utils.resource_monitor import ResourceMonitor

class PixarController:
    """The Controller/Container that manages the interaction between UI and Engine."""
    def __init__(self, state, app):
        self.app_state = state
        self.app = app
        self.renderer = None
        self.renderer_lock = threading.Lock()
        self.comfy_process = None
        
        # Instantiate Visual Processor for previews and cache management
        from core.visual_processor import VisualProcessor
        self.visual_processor = VisualProcessor(cache_size=self.app_state.get_config("cache_size", 8))
        
        # Start Resource Monitor Loop (Default disabled in UI)
        self.app.after(1000, self.refresh_resource_monitor)

    def start_comfy_server(self):
        """Launches the ComfyUI server in a background process."""
        if getattr(self, '_server_starting', False):
            return
        self._server_starting = True

        def _task():
            try:
                self.app.after(100, lambda: self.app.update_status("🚀 Starting AI Engine...", "#3498db"))
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                comfy_dir = os.path.join(base_dir, "ComfyUI")
                venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
                
                if not os.path.exists(venv_python):
                    venv_python = os.path.join(base_dir, "venv", "Scripts", "python.exe")
                    if not os.path.exists(venv_python):
                        self.app.after(100, lambda: self.app.update_status("❌ Error: python.exe not found!", "#e74c3c"))
                        self._server_starting = False
                        return

                main_script = os.path.join(comfy_dir, "main.py")
                if not os.path.exists(main_script):
                    self.app.after(100, lambda: self.app.update_status("❌ Error: ComfyUI/main.py not found!", "#e74c3c"))
                    self._server_starting = False
                    return

                # Memory Strategy Flags
                mem_mode = self.app_state.get_config("mem", "smart_boost")
                flags = []
                if mem_mode == "high_vram": flags.append("--high-vram")
                elif mem_mode == "low_vram": flags.append("--lowvram")
                elif mem_mode == "normal": flags.append("--normalvram")

                import subprocess
                self.comfy_process = subprocess.Popen(
                    [venv_python, "main.py"] + flags,
                    cwd=comfy_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # Wait for API to be ready
                import urllib.request
                retries = 30
                while retries > 0:
                    try:
                        urllib.request.urlopen("http://127.0.0.1:8188", timeout=2)
                        print("✅ AI Engine API is online.")
                        self.app.after(100, lambda: self.warm_up_engine(
                            self.app_state.get_config("mem", "smart_boost"),
                            self.app_state.config
                        ))
                        self._server_starting = False
                        return
                    except:
                        retries -= 1
                        time.sleep(1)
                
                self.app.after(100, lambda: self.app.update_status("❌ Error: Engine Timeout!", "#e74c3c"))
                self._server_starting = False
            except Exception as e:
                print(f"❌ Server Start Error: {e}")
                self.app.after(100, lambda msg=str(e): self.app.update_status(f"Error: {msg}", "#e74c3c"))
                self._server_starting = False

        threading.Thread(target=_task, daemon=True).start()

    def stop_comfy_server(self):
        """Forcefully kills the ComfyUI server and performs a deep system purge."""
        print("🛑 Shutting down Pixar AI Engine...")
        if self.comfy_process:
            try:
                import subprocess
                # Force kill the process tree on Windows
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.comfy_process.pid)], 
                               capture_output=True, check=False)
                print("✅ AI Engine process tree terminated.")
            except Exception as e:
                print(f"⚠️ Shutdown warning: {e}")
            self.comfy_process = None
        
        # Deep Memory Reclamation
        try:
            from utils.system_cleaner import SystemCleaner
            print("🧼 Purging System RAM/VRAM...")
            SystemCleaner.deep_purge()
            SystemCleaner.clean_ghosts()
            print("✨ All resources reclaimed.")
        except Exception as e:
            print(f"⚠️ Purge error: {e}")

    def refresh_model_status(self):
        """Fetches model status from renderer and updates UI."""
        if self.renderer:
            try:
                models = self.renderer.get_model_locations()
                if hasattr(self.app, 'sidebar'):
                    self.app.sidebar.update_model_list(models)
            except Exception as e:
                print(f"⚠️ Model Refresh Error: {e}")

    def refresh_resource_monitor(self):
        """Periodically fetches hardware stats if the UI switch is enabled."""
        try:
            if hasattr(self.app, 'main_panel'):
                panel = self.app.main_panel
                if panel.monitor_active_var.get():
                    gpu_info = ResourceMonitor.get_gpu_info()
                    cpu_info = ResourceMonitor.get_cpu_info()
                    panel.update_resource_view(gpu_info, cpu_info)
        except Exception as e:
            print(f"⚠️ Resource Monitor Error: {e}")
            
        # Schedule next update (every 1 second)
        self.app.after(1000, self.refresh_resource_monitor)

    def warm_up_engine(self, memory_mode, custom_config):
        """Safely initializes the AI engine in a background thread."""
        if getattr(self, 'warmup_in_progress', False):
            return
            
        self.warmup_in_progress = True
        
        def _task():
            try:
                # Proactive Check: Is ComfyUI already running?
                import urllib.request
                is_online = False
                try:
                    urllib.request.urlopen("http://127.0.0.1:8188", timeout=1)
                    is_online = True
                except:
                    is_online = False

                if is_online:
                    print("📡 ComfyUI detected. Proceeding with warm-up.")
                else:
                    print("🛠️ ComfyUI not detected. Starting server...")
                    self.app.after(10, self.start_comfy_server)
                    self.warmup_in_progress = False
                    return

                print(f"🚀 Warm-up Started. Mode: {memory_mode}")
                self.app_state.ui_locked = True
                self.app.after(0, lambda: self.app.update_ui_state("disabled"))
                
                from utils.system_cleaner import SystemCleaner
                SystemCleaner.deep_purge()
                self.app.after(0, lambda: self.app.update_status("🧹 Deep Cleaning RAM...", "#f1c40f"))
                
                with self.renderer_lock:
                    if self.renderer:
                        self.renderer.unload()
                    
                    from core.renderer import PixarRenderer
                    self.renderer = PixarRenderer(
                        memory_management=memory_mode,
                        custom_config=custom_config
                    )
                    
                    # Sync Availability to UI
                    avail = self.renderer.availability
                    if hasattr(self.app, 'sidebar'):
                        # Important: Pass a copy of avail to avoid closure issues
                        self.app.after(0, lambda a=dict(avail): self.app.sidebar.set_availability(a))
                    if hasattr(self.app, 'main_panel'):
                        self.app.after(0, lambda a=dict(avail): self.app.main_panel.set_engine_availability(a.get("unet", False)))
                
                self.app.after(0, lambda: self.app.update_status("Status: Engine Ready", "#2ecc71"))
                self.app_state.ui_locked = False
                self.app.after(0, lambda: self.app.update_ui_state("normal"))
            except Exception as e:
                import traceback
                print(f"❌ Warm-up Connection Failed: {e}")
                
                # If connection refused, try starting the server
                if "[WinError 10061]" in str(e):
                    print("🛠️ Attempting to start AI Engine server automatically...")
                    self.app.after(0, self.start_comfy_server)
                else:
                    print(f"❌ Warm-up Error: {traceback.format_exc()}")
                    self.app.after(0, lambda msg=str(e): self.app.update_status(f"Error: {msg}", "#e74c3c"))
                    self.app.after(0, lambda: self.app.update_ui_state("normal"))
            finally:
                self.warmup_in_progress = False

        threading.Thread(target=_task, daemon=True).start()

    def start_render(self):
        self.app_state.stop_requested = False

        # [CRITICAL] Read ALL Tkinter widgets from the main thread BEFORE spawning background thread
        prompt_text = self.app.art_studio.expert_prompt.get("0.0", "end").strip()
        neg_prompt_text = self.app.art_studio.neg_prompt_entry.get("0.0", "end").strip()
        freeu_params = None

        self.app.update_ui_state("disabled")
        threading.Thread(target=self.run_engine, args=(prompt_text, neg_prompt_text, freeu_params), daemon=True).start()

    def stop_render(self):
        self.app_state.stop_requested = True

    def run_engine(self, prompt_text, neg_prompt_text, freeu_params):
        try:
            if not self.renderer:
                self.app.update_status("⚠️ AI Engine not ready!", "#e74c3c")
                return

            cfg = self.app_state.config
            in_dir = cfg.get("input")
            out_dir = cfg.get("output")
            
            if not in_dir or not out_dir:
                self.app.update_status("⚠️ Please select input/output paths!", "#e74c3c")
                return

            # Prepare Params (widget values already read from main thread)
            base_params = {
                "prompt": prompt_text,
                "neg_prompt": neg_prompt_text,
                "strength": cfg.get("strength", 0.7),
                "denoise": cfg.get("denoise", 0.75),
                "ref_strength": cfg.get("ref_strength", 0.5),
                "steps": int(cfg.get("steps", 6)),
                "guidance_scale": cfg.get("guidance_scale", 2.0),
                "use_canny": cfg.get("use_canny", False),
                "use_depth": cfg.get("use_depth", True),
                "use_ip_adapter": cfg.get("use_ip_adapter", False),
                "use_segment": cfg.get("use_segment", False),
                "depth_strength": cfg.get("depth_strength", 0.65),
                "segment_strength": cfg.get("segment_strength", 0.5),
                "canny_params": {
                    "low": cfg.get("canny_low", 100),
                    "high": cfg.get("canny_high", 200),
                    "auto": cfg.get("auto_canny", False)
                },
                "freeu_params": freeu_params
            }

            active_loras = {}
            from core.lora_registry import LORA_CATALOG
            for lora_name in LORA_CATALOG:
                if cfg.get(f"{lora_name}_enabled", False):
                    active_loras[lora_name] = cfg.get(f"{lora_name}_strength", LORA_CATALOG[lora_name]["strength"])
            base_params["active_loras"] = active_loras

            # Frame Loop Logic
            is_random_seed = cfg.get("random_seed", True)
            fixed_seed = int(cfg.get("seed", 42))
            all_files = os.listdir(in_dir)
            numeric_vals = [int(os.path.splitext(f)[0]) for f in all_files if os.path.splitext(f)[0].isdigit()]
            if not numeric_vals:
                self.app.update_status("❌ No valid frames found!", "#e74c3c")
                return

            current_num = min(numeric_vals)
            gap_counter = 0
            processed_frames = 0 # Counter for seed increment logic
            
            self.app.main_panel.set_render_state(True)
            self.app.update_status("🚀 Rendering...", "white")

            # Pre-map numbers to actual filenames to handle padding (e.g. 0001.png)
            file_map = {}
            for f in all_files:
                base, ext = os.path.splitext(f)
                if base.isdigit() and ext.lower() in SUPPORTED_EXTENSIONS:
                    file_map[int(base)] = f

            while not self.app_state.stop_requested and gap_counter < GAP_LIMIT:
                if current_num in file_map:
                    filename = file_map[current_num]
                    # Determine seed for this specific frame
                    if is_random_seed:
                        frame_seed = random.randint(0, 2**32 - 1)
                    else:
                        increment = processed_frames // 300
                        frame_seed = fixed_seed + increment
                        
                    self.app.update_status(f"🎨 Frame: {current_num} | Seed: {frame_seed}", "white")
                    
                    # Call Renderer
                    self.renderer.render_batch(
                        input_folder=in_dir, 
                        output_folder=out_dir, 
                        specific_file=filename,
                        seed=frame_seed,
                        **base_params
                    )
                    
                    gap_counter = 0
                    processed_frames += 1
                    current_num += 1
                else:
                    gap_counter += 1
                    current_num += 1
                    # Small sleep to prevent UI freeze if many gaps
                    if gap_counter % 1000 == 0: time.sleep(0.01)
        except Exception as e:
            self.app.update_status(f"Error: {str(e)}", "#e74c3c")
            traceback.print_exc()
        finally:
            self.app.main_panel.set_render_state(False)
            self.app.update_status("Status: Done", "#2ecc71")
            self.app.update_ui_state("normal")
            
    def handle_strength_change(self, val):
        self.app_state.update_config("strength", val)
        if hasattr(self.app, 'main_panel'):
            self.app.main_panel.strength_label.configure(text=f"Value: {val:.2f}")
        self.save_config()


    def handle_ref_change(self, val):
        self.app_state.update_config("ref_strength", val)
        if hasattr(self.app, 'main_panel'):
            self.app.main_panel.ref_strength_label.configure(text=f"🎨 IP-Adapter Influence: {val:.2f}")
        self.save_config()

    def handle_guidance_change(self, val):
        self.app_state.update_config("guidance_scale", val)
        if hasattr(self.app, 'art_studio'):
            self.app.art_studio.guidance_label.configure(text=f"{val:.1f}")
        self.save_config()

    def handle_steps_change(self, val):
        self.app_state.update_config("steps", int(val))
        if hasattr(self.app, 'art_studio'):
            self.app.art_studio.steps_label.configure(text=str(int(val)))
        self.save_config()

    def handle_mem_change(self, val):
        """Maps UI selection to ComfyUI CLI flags and saves to config."""
        mapping = {
            "Smart Boost ⚡": "smart_boost",
            "King (TensorRT) 👑": "high_vram",
            "Normal 🚀": "normal",
            "Eco Mode 💾": "low_vram"
        }
        actual_mode = mapping.get(val, "smart_boost")
        
        self.app_state.update_config("mem", actual_mode)
        self.save_config()
        
        # If server is running, inform user it needs restart for physical memory change
        if getattr(self, 'comfy_process', None):
            self.app.update_status("⚠️ Restart required for VRAM strategy change.", "#f1c40f")
        
        # Trigger engine warm-up update
        self.warm_up_engine(actual_mode, self.app_state.config)

    def save_config(self, delay_visual=False):
        """Saves config."""
        self.app.config_manager.save(self.app_state.config)

    def handle_engine_toggle(self, key, val):
        """Toggles engine components without full reload if possible."""
        self.app_state.update_config(key, val)
        self.save_config(delay_visual=True)
        
        # Update UI components if needed
        # (Canny state is now handled internally by Sidebar)
            
        # If renderer exists, try to hot-swap instead of full warm-up
        if self.renderer:
            self.app.update_status("⚙️ Hot-swapping Engine Components...", "#3498db")
            threading.Thread(target=self.renderer.hot_swap_components, args=(self.app_state.config,), daemon=True).start()
        else:
            self.warm_up_engine(self.app_state.get_config("mem", "smart_boost"), self.app_state.config)

    def handle_prompt_change(self, key, val):
        """Updates prompt in state and saves with a debounce delay."""
        self.app_state.update_config(key, val)
        self.save_config(delay_visual=True)

    def handle_canny_config_change(self, key, val):
        self.app_state.update_config(key, val)
        if hasattr(self.app, 'sidebar'):
            if key == "canny_low": self.app.sidebar.canny_low_label.configure(text=str(val))
            if key == "canny_high": self.app.sidebar.canny_high_label.configure(text=str(val))
        self.save_config()

    def handle_canny_auto_toggle(self, val):
        self.app_state.update_config("auto_canny", val)
        self.save_config()



    def handle_ghost_cleaning(self):
        """Triggers the ghost process removal logic."""
        count = SystemCleaner.clean_ghosts()
        self.app.update_status(f"💀 Ghost Cleaning Done: {count} processes terminated.", "#2ecc71")


    def handle_seed_change(self, val):
        """Validates and saves the manual seed value."""
        try:
            seed_val = int(val)
            self.app_state.update_config("seed", seed_val)
            self.save_config()
        except ValueError:
            print(f"⚠️ Invalid Seed Value (Must be Integer): {val}")

    def handle_random_seed_toggle(self, val):
        """Toggles between random and fixed seed modes."""
        self.app_state.update_config("random_seed", val)
        if hasattr(self.app, 'main_panel'):
            self.app.main_panel.update_seed_entry_state(val)
        self.save_config()

    def handle_upscale_toggle(self, val):
        """Toggles the 2x upscale post-processing."""
        self.app_state.update_config("upscale", val)
        self.save_config()

    def handle_config_change(self, key, val):
        """Universal handler for simple config numeric changes."""
        self.app_state.update_config(key, val)
        if hasattr(self.app, 'sidebar'):
            if key == "depth_strength":
                if hasattr(self.app.sidebar, 'depth_str_val_label'):
                    self.app.sidebar.depth_str_val_label.configure(text=f"{val:.2f}")
            elif key == "canny_low":
                if hasattr(self.app.sidebar, 'canny_low_label'):
                    self.app.sidebar.canny_low_label.configure(text=str(int(val)))
            elif key == "canny_high":
                if hasattr(self.app.sidebar, 'canny_high_label'):
                    self.app.sidebar.canny_high_label.configure(text=str(int(val)))
            elif key == "strength":
                if hasattr(self.app.sidebar, 'canny_str_val_label'):
                    self.app.sidebar.canny_str_val_label.configure(text=f"{val:.2f}")
            elif key == "ref_strength":
                if hasattr(self.app.sidebar, 'ip_str_val_label'):
                    self.app.sidebar.ip_str_val_label.configure(text=f"{val:.2f}")
            elif key == "segment_strength":
                if hasattr(self.app.sidebar, 'seg_str_val_label'):
                    self.app.sidebar.seg_str_val_label.configure(text=f"{val:.2f}")

        self.save_config(delay_visual=True)

    def handle_lora_toggle(self, lora_name, val):
        self.app_state.update_config(f"{lora_name}_enabled", val == 1)
        self.save_config()

    def handle_lora_strength(self, lora_name, val):
        self.app_state.update_config(f"{lora_name}_strength", float(val))
        self.save_config()
