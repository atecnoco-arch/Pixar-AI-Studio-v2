import customtkinter as ctk
from core.constants import THEME_BG_DEEP, THEME_BG_PANEL, THEME_PRIMARY, THEME_ACCENT, THEME_TEXT_BOLD, THEME_TEXT_MUTED

class MainPanelComponent:
    """Presentational Component for the Middle Column (Rendering Controls)."""
    def __init__(self, parent, controller, lang_manager):
        self.parent = parent
        self.controller = controller
        self.lang = lang_manager
        self.app_state = controller.app_state
        
        self.frame = ctk.CTkScrollableFrame(parent, fg_color=THEME_BG_DEEP)
        self.frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=20)
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.setup_ui()

    def setup_ui(self):
        m_row = 0
        
        # Dashboard Header
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_frame.grid(row=m_row, column=0, sticky="ew", padx=10, pady=(0, 10))
        ctk.CTkLabel(header_frame, text="🎨 استودیو رندر هوشمند", font=("Inter", 24, "bold"), text_color=THEME_PRIMARY).pack(side="left", padx=10)
        

        m_row += 1
        
        # Big Render Button
        self.render_btn = ctk.CTkButton(self.frame, text=self.lang.get("render_btn"), 
                                        height=70, font=("Inter", 20, "bold"), 
                                        command=self.controller.start_render)
        self.render_btn.grid(row=m_row, column=0, pady=(0, 5), sticky="ew", padx=10)
        m_row += 1

        # Status Label
        self.status_label = ctk.CTkLabel(self.frame, text=self.lang.get("status_online"), font=("Inter", 13))
        self.status_label.grid(row=m_row, column=0, pady=(0, 15))
        m_row += 1


        # Path Selection
        path_frame = ctk.CTkFrame(self.frame, fg_color=THEME_BG_PANEL, corner_radius=15)
        path_frame.grid(row=m_row, column=0, sticky="ew", padx=10, pady=10)
        path_frame.grid_columnconfigure(0, weight=1)
        m_row += 1
        
        self.input_entry = ctk.CTkEntry(path_frame, fg_color="#1a1a1a", border_color="#30363d", text_color=THEME_TEXT_BOLD)
        self.input_entry.insert(0, self.app_state.get_config("input", ""))
        self.input_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(path_frame, text=self.lang.get("browse_in"), width=120, fg_color=THEME_PRIMARY,
                      command=self.controller.app.browse_input).grid(row=0, column=1, padx=10)
        
        self.output_entry = ctk.CTkEntry(path_frame, fg_color="#1a1a1a", border_color="#30363d", text_color=THEME_TEXT_BOLD)
        self.output_entry.insert(0, self.app_state.get_config("output", ""))
        self.output_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        ctk.CTkButton(path_frame, text=self.lang.get("browse_out"), width=120, fg_color=THEME_PRIMARY,
                      command=self.controller.app.browse_output).grid(row=1, column=1, padx=10)

        # SEED & UPSCALE
        tools_frame = ctk.CTkFrame(self.frame, fg_color=THEME_BG_PANEL, corner_radius=15)
        tools_frame.grid(row=m_row, column=0, sticky="ew", padx=10, pady=10)
        m_row += 1
        
        ctk.CTkLabel(tools_frame, text="🎲 Seed:", font=("Inter", 12, "bold"), text_color=THEME_TEXT_BOLD).grid(row=0, column=0, padx=10, pady=10)
        self.seed_entry = ctk.CTkEntry(tools_frame, width=120, fg_color="#1a1a1a", border_color="#30363d", text_color=THEME_TEXT_BOLD)
        self.seed_entry.insert(0, str(self.app_state.get_config("seed", 42)))
        self.seed_entry.grid(row=0, column=1, padx=5)
        # Bindings for seed entry
        self.seed_entry.bind("<FocusOut>", lambda e: self.controller.handle_seed_change(self.seed_entry.get()))
        self.seed_entry.bind("<Return>", lambda e: self.controller.handle_seed_change(self.seed_entry.get()))
        
        self.random_seed_var = ctk.BooleanVar(value=self.app_state.get_config("random_seed", True))
        self.random_seed_checkbox = ctk.CTkCheckBox(tools_frame, text="Random", variable=self.random_seed_var, 
                         font=("Inter", 12), text_color=THEME_TEXT_BOLD,
                         command=lambda: self.controller.handle_random_seed_toggle(self.random_seed_var.get()))
        self.random_seed_checkbox.grid(row=0, column=2, padx=10)
        
        self.upscale_var = ctk.BooleanVar(value=self.app_state.get_config("upscale", False))
        ctk.CTkSwitch(tools_frame, text=self.lang.get("upscale"), variable=self.upscale_var,
                       font=("Inter", 12, "bold"), text_color=THEME_PRIMARY,
                       command=lambda: self.controller.handle_upscale_toggle(self.upscale_var.get())).grid(row=0, column=3, padx=20)

        # Initial state sync
        self.update_seed_entry_state(self.random_seed_var.get())

        # SYSTEM RESOURCE MONITORING
        m_row += 1
        mon_header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        mon_header_frame.grid(row=m_row, column=0, sticky="ew", padx=10, pady=(20, 5))
        
        ctk.CTkLabel(mon_header_frame, text=self.lang.get("sys_mon"), font=("Inter", 14, "bold"), text_color=THEME_ACCENT).pack(side="left")
        m_row += 1
        
        self.monitor_active_var = ctk.BooleanVar(value=False)
        self.monitor_switch = ctk.CTkSwitch(mon_header_frame, text="Live", variable=self.monitor_active_var, 
                                            width=40, text_color=THEME_TEXT_BOLD, progress_color=THEME_ACCENT,
                                            command=self.toggle_monitor_visibility)
        self.monitor_switch.pack(side="right")
        
        m_row += 1
        self.monitor_frame = ctk.CTkFrame(self.frame, fg_color=THEME_BG_PANEL, corner_radius=15)
        # Initial state: hidden if monitor_active_var is False
        self.toggle_monitor_visibility()
        self.monitor_frame.grid_columnconfigure((0, 1), weight=1)
        
        # GPU Stats
        gpu_box = ctk.CTkFrame(self.monitor_frame, fg_color="transparent")
        gpu_box.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(gpu_box, text="🎮 NVIDIA GPU", font=("Inter", 11, "bold"), text_color=THEME_PRIMARY).pack(anchor="w")
        
        self.vram_bar = ctk.CTkProgressBar(gpu_box, height=8, progress_color="#2ecc71")
        self.vram_bar.set(0)
        self.vram_bar.pack(fill="x", pady=(5, 2))
        
        self.vram_text = ctk.CTkLabel(gpu_box, text="VRAM: -- / -- MB", font=("Inter", 10), text_color=THEME_TEXT_MUTED)
        self.vram_text.pack(anchor="w")
        
        self.gpu_load_label = ctk.CTkLabel(gpu_box, text="Load: 0% | Temp: 0°C", font=("Inter", 10), text_color=THEME_TEXT_MUTED)
        self.gpu_load_label.pack(anchor="w")
        
        # CPU Stats
        cpu_box = ctk.CTkFrame(self.monitor_frame, fg_color="transparent")
        cpu_box.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(cpu_box, text="🧠 Processor (CPU)", font=("Inter", 11, "bold"), text_color=THEME_PRIMARY).pack(anchor="w")
        
        self.cpu_bar = ctk.CTkProgressBar(cpu_box, height=8, progress_color="#3498db")
        self.cpu_bar.set(0)
        self.cpu_bar.pack(fill="x", pady=(5, 2))
        
        self.cpu_load_label = ctk.CTkLabel(cpu_box, text="Load: 0% | Temp: 0°C", font=("Inter", 10), text_color=THEME_TEXT_MUTED)
        self.cpu_load_label.pack(anchor="w")

    def update_resource_view(self, gpu_data, cpu_data):
        """Updates the monitoring UI with fresh data."""
        if gpu_data:
            perc = gpu_data.get("vram_perc", 0)
            self.vram_bar.set(perc)
            # Dynamic color based on load
            from utils.resource_monitor import ResourceMonitor
            self.vram_bar.configure(progress_color=ResourceMonitor.get_color(perc))
            
            self.vram_text.configure(text=f"VRAM: {gpu_data['vram_used']} / {gpu_data['vram_total']} MB")
            self.gpu_load_label.configure(text=f"Load: {gpu_data['load']}% | Temp: {gpu_data['temp']}°C")
        
        if cpu_data:
            perc = cpu_data.get("load", 0) / 100.0
            self.cpu_bar.set(perc)
            self.cpu_bar.configure(progress_color=ResourceMonitor.get_color(perc))
            self.cpu_load_label.configure(text=f"Load: {cpu_data['load']}% | Temp: {cpu_data['temp']}°C")

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)

    def set_render_state(self, is_rendering):
        if is_rendering:
            self.render_btn.configure(text="STOP", fg_color="#c0392b")
        else:
            self.render_btn.configure(text=self.lang.get("render_btn"), fg_color=THEME_PRIMARY)

    def set_engine_availability(self, available):
        """Disables the render button and shows an error if the engine is not ready."""
        if not available:
            self.render_btn.configure(state="disabled", fg_color="#e74c3c", text=self.lang.get("engine_missing"))
            self.status_label.configure(text=self.lang.get("engine_missing"), text_color="#e74c3c")
        else:
            self.render_btn.configure(state="normal", fg_color=THEME_PRIMARY, text=self.lang.get("render_btn"))
            self.status_label.configure(text=self.lang.get("status_online"), text_color="white")

    def update_seed_entry_state(self, is_random):
        """Disables Seed entry if Random is ON, enables otherwise."""
        if is_random:
            self.seed_entry.configure(state="disabled", fg_color="#2b2b2b", text_color="#555")
        else:
            self.seed_entry.configure(state="normal", fg_color="#1a1a1a", text_color=THEME_TEXT_BOLD)


    def toggle_monitor_visibility(self):
        """Shows or hides the resource monitoring panel."""
        if self.monitor_active_var.get():
            self.monitor_frame.grid(row=11, column=0, sticky="ew", padx=10, pady=(0, 20))
        else:
            self.monitor_frame.grid_forget()
