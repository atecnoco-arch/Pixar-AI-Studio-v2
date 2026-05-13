import customtkinter as ctk
from core.constants import THEME_BG_DEEP, THEME_PRIMARY, THEME_ACCENT, THEME_TEXT_BOLD, THEME_TEXT_MUTED

class ArtStudioComponent:
    """Presentational Component for the Artistic Studio (Prompts & Tech Settings)."""
    def __init__(self, parent, controller, lang_manager):
        self.parent = parent
        self.controller = controller
        self.lang = lang_manager
        self.app_state = controller.app_state
        
        self.frame = ctk.CTkScrollableFrame(parent, corner_radius=0, fg_color=THEME_BG_DEEP)
        self.frame.grid(row=0, column=2, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        
        # History State
        self.history = {
            "negative_prompt": {"data": [], "index": -1},
            "expert_prompt": {"data": [], "index": -1}
        }
        
        self.setup_ui()

    def setup_ui(self):
        r_row = 0
        ctk.CTkLabel(self.frame, text=self.lang.get("artistic_studio"), 
                     font=("Inter", 16, "bold"), text_color=THEME_ACCENT).grid(row=r_row, column=0, padx=20, pady=(15, 5))
        r_row += 1

        # Prompts
        prompts_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        prompts_container.grid(row=r_row, column=0, sticky="ew", padx=20, pady=5)
        prompts_container.grid_columnconfigure(0, weight=1)
        r_row += 1

        # Negative Prompt
        neg_header = ctk.CTkFrame(prompts_container, fg_color="transparent")
        neg_header.grid(row=0, column=0, pady=(10, 0), sticky="w,e")
        ctk.CTkLabel(neg_header, text=self.lang.get("neg_prompt"), font=("Inter", 13, "bold"), text_color=THEME_TEXT_BOLD).pack(side="left")
        
        # Undo / Redo for Negative Prompt
        self.neg_undo_btn = ctk.CTkButton(neg_header, text="↩", width=30, height=24, fg_color="#333", hover_color=THEME_PRIMARY, command=lambda: self.undo_prompt("negative_prompt"))
        self.neg_undo_btn.pack(side="left", padx=(10, 2))
        self.neg_redo_btn = ctk.CTkButton(neg_header, text="↪", width=30, height=24, fg_color="#333", hover_color=THEME_PRIMARY, command=lambda: self.redo_prompt("negative_prompt"))
        self.neg_redo_btn.pack(side="left", padx=2)
        
        initial_neg = self.app_state.get_config("negative_prompt", "")
        self.history["negative_prompt"]["data"] = [initial_neg]
        self.history["negative_prompt"]["index"] = 0
        
        self.neg_prompt_entry = ctk.CTkTextbox(prompts_container, height=100, font=("Inter", 12), 
                                               fg_color="#1a1a1a", border_color="#e74c3c", border_width=1, text_color=THEME_TEXT_BOLD)
        self.neg_prompt_entry.insert("0.0", initial_neg)
        self.neg_prompt_entry.grid(row=1, column=0, pady=(5, 10), sticky="ew")
        
        # Enhanced bindings for saving
        for event in ["<KeyRelease>", "<<Paste>>", "<<Cut>>"]:
            self.neg_prompt_entry.bind(event, lambda e: self.on_prompt_type("negative_prompt", self.neg_prompt_entry.get("0.0", "end").strip()))
        
        # Right-click context menu
        self.add_context_menu(self.neg_prompt_entry)

        # Expert Prompt
        expert_header = ctk.CTkFrame(prompts_container, fg_color="transparent")
        expert_header.grid(row=2, column=0, pady=(5, 0), sticky="w,e")
        ctk.CTkLabel(expert_header, text=self.lang.get("expert_prompt"), 
                     font=("Inter", 14, "bold"), text_color=THEME_ACCENT).pack(side="left")

        # Undo / Redo for Expert Prompt
        self.exp_undo_btn = ctk.CTkButton(expert_header, text="↩", width=30, height=24, fg_color="#333", hover_color=THEME_PRIMARY, command=lambda: self.undo_prompt("expert_prompt"))
        self.exp_undo_btn.pack(side="left", padx=(10, 2))
        self.exp_redo_btn = ctk.CTkButton(expert_header, text="↪", width=30, height=24, fg_color="#333", hover_color=THEME_PRIMARY, command=lambda: self.redo_prompt("expert_prompt"))
        self.exp_redo_btn.pack(side="left", padx=2)
        
        initial_exp = self.app_state.get_config("expert_prompt", "")
        self.history["expert_prompt"]["data"] = [initial_exp]
        self.history["expert_prompt"]["index"] = 0

        self.expert_prompt = ctk.CTkTextbox(prompts_container, height=100, font=("Inter", 12), 
                                             fg_color="#1a1a1a", border_color=THEME_PRIMARY, border_width=1, text_color=THEME_TEXT_BOLD)
        self.expert_prompt.grid(row=3, column=0, pady=5, sticky="ew")
        self.expert_prompt.insert("0.0", initial_exp)
        
        # Enhanced bindings for saving
        for event in ["<KeyRelease>", "<<Paste>>", "<<Cut>>"]:
            self.expert_prompt.bind(event, lambda e: self.on_prompt_type("expert_prompt", self.expert_prompt.get("0.0", "end").strip()))
        
        self.add_context_menu(self.expert_prompt)
        
        # Technical Sliders (Guidance, Steps, etc.)
        self.setup_tech_sliders(r_row)

    def on_prompt_type(self, prompt_key, text):
        h = self.history[prompt_key]
        if h["data"] and h["data"][h["index"]] != text:
            # Check if this isn't just a minor typing change (like one char). For simplicity we'll push on space or specific boundaries.
            # But simpler approach: just debounce it in controller as before, and update history here only if length diff > 3 or last char is space to avoid 1char history
            if len(h["data"]) > 0 and abs(len(h["data"][-1]) - len(text)) > 3 or text.endswith(" ") or text.endswith(","):
                # truncate future history if we type something new
                h["data"] = h["data"][:h["index"]+1]
                h["data"].append(text)
                h["index"] = len(h["data"]) - 1
                # limit history size
                if len(h["data"]) > 50:
                    h["data"].pop(0)
                    h["index"] -= 1

        self.controller.handle_prompt_change(prompt_key, text)
        self.update_history_btns()

    def undo_prompt(self, prompt_key):
        h = self.history[prompt_key]
        if h["index"] > 0:
            h["index"] -= 1
            text = h["data"][h["index"]]
            self._set_prompt_text(prompt_key, text)
            self.controller.handle_prompt_change(prompt_key, text)
        self.update_history_btns()

    def redo_prompt(self, prompt_key):
        h = self.history[prompt_key]
        if h["index"] < len(h["data"]) - 1:
            h["index"] += 1
            text = h["data"][h["index"]]
            self._set_prompt_text(prompt_key, text)
            self.controller.handle_prompt_change(prompt_key, text)
        self.update_history_btns()
        
    def _set_prompt_text(self, key, text):
        widget = self.neg_prompt_entry if key == "negative_prompt" else self.expert_prompt
        widget.delete("0.0", "end")
        widget.insert("0.0", text)

    def update_history_btns(self):
        # Could grey out buttons if at start/end of history, but simple implementation is fine
        pass

    def setup_tech_sliders(self, r_row):
        # Guidance Scale
        guidance_header = ctk.CTkFrame(self.frame, fg_color="transparent")
        guidance_header.grid(row=r_row, column=0, padx=25, pady=(10,0), sticky="w")
        r_row += 1
        ctk.CTkLabel(guidance_header, text=self.lang.get("guidance_scale"), font=("Inter", 13, "bold"), text_color=THEME_TEXT_BOLD).pack(side="left")
        self.guidance_label = ctk.CTkLabel(guidance_header, text=f"{self.app_state.get_config('guidance_scale', 1.5):.1f}", 
                                           font=("Inter", 12, "bold"), text_color=THEME_PRIMARY)
        self.guidance_label.pack(side="left", padx=5)
        
        self.guidance_slider = ctk.CTkSlider(self.frame, from_=1.0, to=12.0, 
                                             command=self.controller.handle_guidance_change)
        self.guidance_slider.set(self.app_state.get_config("guidance_scale", 1.5))
        self.guidance_slider.grid(row=r_row, column=0, padx=20, pady=(3, 5), sticky="ew")
        r_row += 1

        # Steps
        steps_header = ctk.CTkFrame(self.frame, fg_color="transparent")
        steps_header.grid(row=r_row, column=0, padx=25, pady=(5,0), sticky="w")
        r_row += 1
        ctk.CTkLabel(steps_header, text=self.lang.get("render_steps"), font=("Inter", 13, "bold"), text_color=THEME_TEXT_BOLD).pack(side="left")
        self.steps_label = ctk.CTkLabel(steps_header, text=str(int(self.app_state.get_config('steps', 8))), 
                                        font=("Inter", 12, "bold"), text_color=THEME_PRIMARY)
        self.steps_label.pack(side="left", padx=5)
        
        self.steps_slider = ctk.CTkSlider(self.frame, from_=1, to=40, number_of_steps=39, 
                                          command=self.controller.handle_steps_change)
        self.steps_slider.set(self.app_state.get_config("steps", 8))
        self.steps_slider.grid(row=r_row, column=0, padx=20, pady=(3, 5), sticky="ew")
        r_row += 1

        # Denoise
        denoise_header = ctk.CTkFrame(self.frame, fg_color="transparent")
        denoise_header.grid(row=r_row, column=0, padx=25, pady=(5,0), sticky="w")
        r_row += 1
        ctk.CTkLabel(denoise_header, text="🔥 " + self.lang.get("denoise", "قدرت تغییرات (Denoise)"), font=("Inter", 13, "bold"), text_color=THEME_TEXT_BOLD).pack(side="left")
        self.denoise_label = ctk.CTkLabel(denoise_header, text=f"{self.app_state.get_config('denoise', 0.75):.2f}", 
                                          font=("Inter", 12, "bold"), text_color=THEME_PRIMARY)
        self.denoise_label.pack(side="left", padx=5)
        
        self.denoise_slider = ctk.CTkSlider(self.frame, from_=0.0, to=1.0, 
                                            command=lambda v: self._update_denoise(float(v)))
        self.denoise_slider.set(self.app_state.get_config("denoise", 0.75))
        self.denoise_slider.grid(row=r_row, column=0, padx=20, pady=(3, 10), sticky="ew")
        r_row += 1

    def _update_denoise(self, val):
        self.denoise_label.configure(text=f"{val:.2f}")
        self.controller.handle_config_change("denoise", val)


    def add_context_menu(self, widget):
        """Adds a professional right-click menu for Copy/Paste/Clear."""
        import tkinter as tk
        def show_menu(event):
            m = tk.Menu(widget, tearoff=0, bg="#1a1d23", fg="white", activebackground=THEME_PRIMARY)
            m.add_command(label="کپی (Copy)", command=lambda: self._do_copy(widget))
            m.add_command(label="چسباندن (Paste)", command=lambda: self._do_paste(widget))
            m.add_separator()
            m.add_command(label="پاک کردن (Clear)", command=lambda: widget.delete("0.0", "end"))
            m.post(event.x_root, event.y_root)
            
        # Bind to the underlying CTK textbox component for reliability
        widget._textbox.bind("<Button-3>", show_menu)

    def _do_copy(self, widget):
        try:
            selected_text = widget.get("sel.first", "sel.last")
            self.parent.clipboard_clear()
            self.parent.clipboard_append(selected_text)
        except tk.TclError:
            pass # No selection

    def _do_paste(self, widget):
        try:
            text = self.parent.clipboard_get()
            widget.insert("insert", text)
            # Trigger save logic manually after paste
            key = "negative_prompt" if widget == self.neg_prompt_entry else "expert_prompt"
            self.on_prompt_type(key, widget.get("0.0", "end").strip())
        except tk.TclError:
            pass
