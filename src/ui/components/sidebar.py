import customtkinter as ctk
import os
from PIL import Image
from core.constants import SUPPORTED_EXTENSIONS, THEME_BG_DEEP, THEME_BG_PANEL, THEME_PRIMARY, THEME_ACCENT, THEME_TEXT_BOLD, THEME_TEXT_MUTED

class SidebarComponent:
    """Presentational Component for the Left Sidebar."""
    def __init__(self, parent, controller, lang_manager):
        self.parent = parent
        self.controller = controller
        self.lang = lang_manager
        self.app_state = controller.app_state
        
        self.frame = ctk.CTkScrollableFrame(parent, corner_radius=0, fg_color=THEME_BG_DEEP)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.setup_ui()

    def setup_ui(self):
        # Sidebar Title
        ctk.CTkLabel(self.frame, text=self.lang.get("sidebar_title"), 
                     font=("Inter", 26, "bold"), text_color=THEME_PRIMARY).grid(row=0, column=0, padx=20, pady=(30, 10))

        # Language Selection
        lang_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        lang_frame.grid(row=1, column=0, padx=25, pady=(0, 15), sticky="w")
        ctk.CTkLabel(lang_frame, text="🌐 Language:", font=("Inter", 11), text_color=THEME_TEXT_MUTED).pack(side="left")
        self.lang_menu = ctk.CTkOptionMenu(lang_frame, values=["fa", "en", "tr", "ar"], 
                                           width=80, height=22, command=self.controller.app.change_language)
        self.lang_menu.set(self.lang.current_lang)
        self.lang_menu.pack(side="left", padx=5)

        
        # Memory Strategy
        mem_header = ctk.CTkFrame(self.frame, fg_color="transparent")
        mem_header.grid(row=3, column=0, padx=25, pady=(15,0), sticky="w")
        ctk.CTkLabel(mem_header, text=self.lang.get("mem_strategy"), font=("Inter", 13, "bold"), text_color=THEME_TEXT_BOLD).pack(side="left")
        
        self.mem_menu = ctk.CTkOptionMenu(self.frame, values=["Smart Boost ⚡", "King (TensorRT) 👑", "Normal 🚀", "Eco Mode 💾"], 
                                           command=self.controller.handle_mem_change)
        saved_mem = self.app_state.get_config("mem", "smart_boost")
        display_mapping = {
            "smart_boost": "Smart Boost ⚡",
            "high_vram": "King (TensorRT) 👑",
            "normal": "Normal 🚀",
            "low_vram": "Eco Mode 💾"
        }
        self.mem_menu.set(display_mapping.get(saved_mem, "Smart Boost ⚡"))
        self.mem_menu.grid(row=4, column=0, padx=20, pady=(5, 10), sticky="ew")

        # ControlNet Engine Selection
        ctk.CTkLabel(self.frame, text=self.lang.get("engine_comp"), font=("Inter", 13, "bold"), text_color=THEME_TEXT_BOLD).grid(row=5, column=0, padx=25, pady=(15, 5), sticky="w")
        engine_frame = ctk.CTkFrame(self.frame, fg_color=THEME_BG_PANEL, corner_radius=10)
        engine_frame.grid(row=6, column=0, padx=15, pady=5, sticky="ew")
        
        # 1. DEPTH SECTION
        self.use_depth_var = ctk.BooleanVar(value=self.app_state.get_config("use_depth", True))
        self.depth_sw = ctk.CTkSwitch(engine_frame, text=self.lang.get("depth_toggle"), variable=self.use_depth_var, 
                       font=("Inter", 11, "bold"), text_color=THEME_TEXT_BOLD,
                       command=self.toggle_depth_manual)
        self.depth_sw.pack(anchor="w", padx=10, pady=5)
        
        depth_str_row = ctk.CTkFrame(engine_frame, fg_color="transparent")
        depth_str_row.pack(fill="x", padx=10, pady=(0, 10))
        self.depth_str_label_icon = ctk.CTkLabel(depth_str_row, text="📏 قدرت عمق:", font=("Inter", 10), text_color=THEME_TEXT_MUTED)
        self.depth_str_label_icon.pack(side="left")
        self.depth_str_val_label = ctk.CTkLabel(depth_str_row, text=f"{self.app_state.get_config('depth_strength', 0.65):.2f}", font=("Inter", 10))
        self.depth_str_val_label.pack(side="right")
        
        self.depth_str_slider = ctk.CTkSlider(engine_frame, from_=0.0, to=1.0, height=12,
                                             command=lambda v: self.controller.handle_config_change("depth_strength", float(v)))
        self.depth_str_slider.set(self.app_state.get_config("depth_strength", 0.65))
        self.depth_str_slider.pack(fill="x", padx=10, pady=(0, 10))

        # 2. CANNY SECTION
        self.use_canny_var = ctk.BooleanVar(value=self.app_state.get_config("use_canny", False))
        self.canny_sw = ctk.CTkSwitch(engine_frame, text=self.lang.get("canny_toggle"), variable=self.use_canny_var, 
                       font=("Inter", 11, "bold"), text_color=THEME_TEXT_BOLD,
                       command=self.toggle_canny_manual)
        self.canny_sw.pack(anchor="w", padx=10, pady=5)

        canny_str_row = ctk.CTkFrame(engine_frame, fg_color="transparent")
        canny_str_row.pack(fill="x", padx=10, pady=(0, 5))
        self.canny_str_label_icon = ctk.CTkLabel(canny_str_row, text="✏️ قدرت کنی:", font=("Inter", 10), text_color=THEME_TEXT_MUTED)
        self.canny_str_label_icon.pack(side="left")
        self.canny_str_val_label = ctk.CTkLabel(canny_str_row, text=f"{self.app_state.get_config('strength', 0.25):.2f}", font=("Inter", 10))
        self.canny_str_val_label.pack(side="right")
        
        self.canny_str_slider = ctk.CTkSlider(engine_frame, from_=0.0, to=1.0, height=12,
                                              command=lambda v: self.controller.handle_config_change("strength", float(v)))
        self.canny_str_slider.set(self.app_state.get_config("strength", 0.25))
        self.canny_str_slider.pack(fill="x", padx=10, pady=(0, 10))

        # Canny Advanced Settings
        self.canny_adv_frame = ctk.CTkFrame(engine_frame, fg_color="transparent")
        self.canny_adv_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.canny_auto_var = ctk.BooleanVar(value=self.app_state.get_config("auto_canny", True))
        self.auto_canny_sw = ctk.CTkSwitch(self.canny_adv_frame, text=self.lang.get("auto_mode"), variable=self.canny_auto_var,
                                          font=("Inter", 10), text_color=THEME_TEXT_BOLD, command=self.toggle_canny_manual)
        self.auto_canny_sw.pack(anchor="w", padx=15, pady=2)
        
        low_row = ctk.CTkFrame(self.canny_adv_frame, fg_color="transparent")
        low_row.pack(fill="x", padx=15)
        self.canny_low_title = ctk.CTkLabel(low_row, text=self.lang.get("low"), font=("Inter", 9), text_color=THEME_TEXT_MUTED)
        self.canny_low_title.pack(side="left")
        self.canny_low_label = ctk.CTkLabel(low_row, text=str(self.app_state.get_config("canny_low", 100)), font=("Inter", 9))
        self.canny_low_label.pack(side="right")
        
        self.canny_low_slider = ctk.CTkSlider(self.canny_adv_frame, from_=0, to=255, height=12,
                                             command=lambda v: self.controller.handle_canny_config_change("canny_low", int(v)))
        self.canny_low_slider.set(self.app_state.get_config("canny_low", 100))
        self.canny_low_slider.pack(fill="x", padx=15, pady=(0, 5))
        
        high_row = ctk.CTkFrame(self.canny_adv_frame, fg_color="transparent")
        high_row.pack(fill="x", padx=15)
        self.canny_high_title = ctk.CTkLabel(high_row, text=self.lang.get("high"), font=("Inter", 9), text_color=THEME_TEXT_MUTED)
        self.canny_high_title.pack(side="left")
        self.canny_high_label = ctk.CTkLabel(high_row, text=str(self.app_state.get_config("canny_high", 200)), font=("Inter", 9))
        self.canny_high_label.pack(side="right")
        
        self.canny_high_slider = ctk.CTkSlider(self.canny_adv_frame, from_=0, to=255, height=12,
                                               command=lambda v: self.controller.handle_canny_config_change("canny_high", int(v)))
        self.canny_high_slider.set(self.app_state.get_config("canny_high", 200))
        self.canny_high_slider.pack(fill="x", padx=15, pady=(0, 5))




        # Active Models Section
        ctk.CTkLabel(self.frame, text=self.lang.get("active_models"), font=("Inter", 13, "bold"), text_color=THEME_PRIMARY).grid(row=7, column=0, padx=20, pady=(15, 5), sticky="w")
        self.models_container = ctk.CTkFrame(self.frame, fg_color=THEME_BG_PANEL, corner_radius=10)
        self.models_container.grid(row=8, column=0, padx=15, pady=5, sticky="ew")
        
        self.toggle_depth_manual()
        self.toggle_canny_manual()
        self.parent.after(2000, self.controller.refresh_model_status)

    def toggle_depth_manual(self):
        is_active = self.use_depth_var.get()
        state = "normal" if is_active else "disabled"
        color = THEME_TEXT_BOLD if is_active else THEME_TEXT_MUTED
        self.depth_str_slider.configure(state=state)
        self.depth_str_label_icon.configure(text_color=color)
        self.depth_str_val_label.configure(text_color=color)
        if hasattr(self, 'controller'):
            self.controller.handle_engine_toggle("use_depth", is_active)

    def toggle_canny_manual(self):
        is_active = self.use_canny_var.get()
        is_auto = self.canny_auto_var.get()
        state = "normal" if is_active else "disabled"
        threshold_state = "normal" if (is_active and not is_auto) else "disabled"
        color = THEME_TEXT_BOLD if is_active else THEME_TEXT_MUTED
        
        self.canny_str_slider.configure(state=state)
        self.canny_str_label_icon.configure(text_color=color)
        self.canny_str_val_label.configure(text_color=color)
        
        self.auto_canny_sw.configure(state=state)
        self.canny_low_slider.configure(state=threshold_state)
        self.canny_high_slider.configure(state=threshold_state)
        self.canny_low_title.configure(text_color=THEME_TEXT_BOLD if (is_active and not is_auto) else THEME_TEXT_MUTED)
        self.canny_high_title.configure(text_color=THEME_TEXT_BOLD if (is_active and not is_auto) else THEME_TEXT_MUTED)
        
        if hasattr(self, 'controller'):
            self.controller.handle_canny_auto_toggle(is_auto)
            self.controller.handle_engine_toggle("use_canny", is_active)



    def set_availability(self, tool_or_dict, is_available=None):
        """Unified method for updating tool status. Supports dict or single tool."""
        missing_color = "#e74c3c" # Red
        
        # If dictionary provided (from Controller)
        if isinstance(tool_or_dict, dict):
            for t, avail in tool_or_dict.items():
                self.set_availability(t, avail)
            return

        # Handle Individual Tool logic
        tool = tool_or_dict
        if tool == "ip_adapter":
            pass  # IP-Adapter removed from UI
                
        elif tool in ["canny", "controlnet"]: # Map engine 'controlnet' to UI 'canny' if needed
            if not is_available:
                self.canny_sw.configure(text=f"{self.lang.get('canny_toggle')} (Locked 🔒)", state="disabled", text_color=missing_color)
                self.toggle_canny_manual()
            else:
                self.canny_sw.configure(text=self.lang.get("canny_toggle"), state="normal", text_color=THEME_TEXT_BOLD)
                self.toggle_canny_manual()
        
        elif tool == "depth":
            if not is_available:
                self.depth_sw.configure(text=f"{self.lang.get('depth_toggle')} (Locked 🔒)", state="disabled", text_color=missing_color)
                self.toggle_depth_manual()
            else:
                self.depth_sw.configure(text=self.lang.get("depth_toggle"), state="normal", text_color=THEME_TEXT_BOLD)
                self.toggle_depth_manual()


    def update_model_list(self, models):
        for widget in self.models_container.winfo_children(): widget.destroy()
        for i, (path, info) in enumerate(models.items()):
            color = "#2ecc71" if info["status"] == "gpu" else "#f1c40f" if info["status"] == "ram" else "#7f8c8d"
            icon = "🟢" if info["status"] == "gpu" else "🟡" if info["status"] == "ram" else "⚪"
            row = ctk.CTkFrame(self.models_container, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(row, text=icon, font=("Inter", 10)).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=info["nature"], font=("Inter", 11, "bold"), text_color=color).pack(side="left")
            ctk.CTkLabel(row, text=f"{info['size_mb']/1024:.1f}GB", font=("Inter", 10), text_color="#555").pack(side="right", padx=5)
