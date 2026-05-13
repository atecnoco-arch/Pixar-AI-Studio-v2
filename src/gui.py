import sys
import os
import customtkinter as ctk
import threading
import traceback

# Add src to path if needed
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path: sys.path.append(root_dir)

from utils.config_manager import ConfigManager
from utils.language_manager import LanguageManager
from utils.hardware_detector import HardwareDetector
from core.constants import WINDOW_SIZE, THEME_PRIMARY
from ui.state import AppState
from ui.controller import PixarController

# Import Components
from ui.components.sidebar import SidebarComponent
from ui.components.main_panel import MainPanelComponent
from ui.components.art_studio import ArtStudioComponent
from ui.components.lora_manager import LoRAManagerComponent

class PixarApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Initialize Core Services
        self.config_manager = ConfigManager()
        initial_config = self.config_manager.load()
        self.lang = LanguageManager(default_lang=initial_config.get("lang", "fa"))
        self.hw_info = HardwareDetector.detect()
        
        # 2. Initialize State & Controller
        self.app_state = AppState(initial_config)
        self.controller = PixarController(self.app_state, self)
        
        # 3. Setup Window
        self.title(self.lang.get("app_title"))
        self.geometry(WINDOW_SIZE)
        self.after(100, lambda: self.state_window("zoomed"))
        
        # Grid Configuration (4 Columns)
        self.grid_columnconfigure(0, weight=1) # Sidebar
        self.grid_columnconfigure(1, weight=2) # Main
        self.grid_columnconfigure(2, weight=1) # Art Studio
        self.grid_columnconfigure(3, weight=1) # LoRA Manager
        self.grid_rowconfigure(0, weight=1)

        # 4. Initialize Components
        self.setup_ui()
        
        # 5. Startup Tasks
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(500, lambda: self.controller.warm_up_engine(
            self.app_state.get_config("mem", "smart_boost"),
            self.app_state.config
        ))

    def setup_ui(self):
        """Builds the UI by assembling components."""
        self.sidebar = SidebarComponent(self, self.controller, self.lang)
        self.main_panel = MainPanelComponent(self, self.controller, self.lang)
        self.art_studio = ArtStudioComponent(self, self.controller, self.lang)
        self.lora_manager = LoRAManagerComponent(self, self.controller, self.lang)

    def update_ui_state(self, state):
        """Global UI lock/unlock mechanism."""
        # This will be delegated to components in a real scenario
        # For now, we just update the buttons we have references to
        target = "normal" if state == "normal" else "disabled"
        self.main_panel.render_btn.configure(state=target)

    def update_status(self, text, color="white"):
        self.main_panel.update_status(text, color)

    def change_language(self, new_lang):
        self.lang.set_language(new_lang)
        self.app_state.update_config("lang", new_lang)
        self.config_manager.save(self.app_state.config)
        
        # Rebuild UI
        for widget in self.winfo_children():
            widget.destroy()
        self.setup_ui()

    def browse_input(self):
        f = ctk.filedialog.askdirectory()
        if f:
            self.main_panel.input_entry.delete(0, "end")
            self.main_panel.input_entry.insert(0, f)
            self.app_state.update_config("input", f)
            self.config_manager.save(self.app_state.config)

    def browse_output(self):
        f = ctk.filedialog.askdirectory()
        if f:
            self.main_panel.output_entry.delete(0, "end")
            self.main_panel.output_entry.insert(0, f)
            self.app_state.update_config("output", f)
            self.config_manager.save(self.app_state.config)

    def state_window(self, mode):
        try: self.state(mode)
        except: pass

    def on_closing(self):
        print("🛑 Closing Application...")
        self.controller.stop_render()
        self.controller.stop_comfy_server()
        self.destroy()
        os._exit(0)

if __name__ == "__main__":
    app = PixarApp()
    app.mainloop()
