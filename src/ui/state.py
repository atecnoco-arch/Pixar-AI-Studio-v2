import threading

class AppState:
    """Holds the global state of the Pixar AI Studio application."""
    def __init__(self, config):
        self.config = config
        self.ui_locked = False
        self.stop_requested = False
        self.engine_busy = False
        self.status_text = "Status: Online"
        self.status_color = "#2ecc71"
        self.rendered_count = 0
        self.current_frame = 0
        self.vram_projected_mb = 0
        self.lock = threading.Lock()

    def update_config(self, key, value):
        with self.lock:
            self.config[key] = value

    def get_config(self, key, default=None):
        return self.config.get(key, default)
