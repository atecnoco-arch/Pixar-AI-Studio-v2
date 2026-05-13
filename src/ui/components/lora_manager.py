import customtkinter as ctk
from core.lora_registry import LORA_CATALOG, CATEGORY_COLORS, CATEGORY_ICONS, is_lora_installed
from core.constants import THEME_BG_DEEP, THEME_BG_PANEL, THEME_TEXT_BOLD, THEME_TEXT_MUTED, THEME_PRIMARY

class LoRAManagerComponent:
    """Presentational Component for the LoRA Manager Sidebar."""
    def __init__(self, parent, controller, lang_manager):
        self.parent = parent
        self.controller = controller
        self.lang = lang_manager
        self.app_state = controller.app_state
        
        self.frame = ctk.CTkScrollableFrame(parent, corner_radius=0, fg_color=THEME_BG_DEEP)
        self.frame.grid(row=0, column=3, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self.frame, text="🧩 LoRA Manager", font=("Inter", 20, "bold"), text_color="#2ecc71").pack(pady=(20, 15))
        
        # Consistent categories with lora_registry.py
        for category in ["Texture", "Lighting", "Character", "Environment", "Style"]:
            cat_color = CATEGORY_COLORS.get(category, "#ffffff")
            cat_icon = CATEGORY_ICONS.get(category, "📌")
            ctk.CTkLabel(self.frame, text=f"{cat_icon} {category.title()}", 
                         font=("Inter", 16, "bold"), text_color=cat_color).pack(pady=(15, 5), anchor="w", padx=10)
            
            # Fix: Iterate over dictionary values
            for lora_name, lora_data in LORA_CATALOG.items():
                if lora_data["category"] == category:
                    self.create_lora_card(lora_name, lora_data, cat_color)

    def create_lora_card(self, lora_name, lora_data, cat_color):
        installed = is_lora_installed(lora_name, self.controller.app_state.get_config("models_dir", "models"))
        card_bg = THEME_BG_PANEL if installed else "#090c10"
        border_color = cat_color if installed else "#30363d"
        
        f = ctk.CTkFrame(self.frame, fg_color=card_bg, corner_radius=12, border_width=1, border_color=border_color)
        f.pack(fill="x", padx=10, pady=8)
        
        inner_f = ctk.CTkFrame(f, fg_color="transparent")
        inner_f.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Thumbnail placeholder
        thumb_f = ctk.CTkFrame(inner_f, width=55, height=55, fg_color=cat_color, corner_radius=8)
        thumb_f.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(thumb_f, text=lora_name[0], font=("Inter", 24, "bold"), text_color="#ffffff").pack(expand=True)
        
        info_f = ctk.CTkFrame(inner_f, fg_color="transparent")
        info_f.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(info_f, text=lora_name, font=("Inter", 16, "bold"), text_color=THEME_TEXT_BOLD).pack(anchor="w")
        ctk.CTkLabel(info_f, text=lora_data.get("description", ""), font=("Inter", 11), text_color=THEME_TEXT_MUTED, wraplength=180).pack(anchor="w")
        
        # Toggle and Slider
        ctrl_f = ctk.CTkFrame(info_f, fg_color="transparent")
        ctrl_f.pack(fill="x", pady=(5, 0))
        
        sw = ctk.CTkSwitch(ctrl_f, text="", width=40)
        sw.pack(side="right")
        
        # Check current state from app_state
        is_enabled = self.app_state.get_config(f"{lora_name}_enabled", False)
        if is_enabled and installed:
            sw.select()
        else:
            sw.deselect()
            
        sw.configure(command=lambda l=lora_name: self.controller.handle_lora_toggle(l, sw.get()))
        
        # Strength Slider (per-LoRA range from catalog)
        min_str = lora_data.get("min_strength", 0.0)
        max_str = lora_data.get("max_strength", 2.0)
        current_val = self.app_state.get_config(f"{lora_name}_strength", lora_data.get("strength", 0.8))
        slider_var = ctk.DoubleVar(value=current_val)
        
        val_label = ctk.CTkLabel(ctrl_f, text=f"{current_val:.2f}", font=("Inter", 10, "bold"), text_color=THEME_PRIMARY, width=35)
        val_label.pack(side="left", padx=(5, 5))
        
        slider = ctk.CTkSlider(ctrl_f, variable=slider_var, from_=min_str, to=max_str, width=100, 
                               command=lambda v, l=lora_name, lbl=val_label: self._update_lora_slider(l, float(v), lbl))
        slider.pack(side="left")
        
    def _update_lora_slider(self, lora_name, val, label_widget):
        label_widget.configure(text=f"{val:.2f}")
        self.controller.handle_lora_strength(lora_name, val)
