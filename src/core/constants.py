import os
from pathlib import Path
# Model Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
SOLID_MODELS_DIR = MODELS_DIR / "solid_models"

GAP_LIMIT = 100
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif']
DEFAULT_SEED = 42
NUM_INFERENCE_STEPS = 8                                 

                                                                   
MODEL_MEMORY_MAP = {
    "Text Encoder": 250,                                                                    
    "UNet (Main Denoising)": 4900,                                      
    "ControlNet (Structure)": 1500, # Increased for Union Pro Max                      
    "VAE (Image Decoder)": 320,                                                     
    "Text Encoder": 250                                     
}

                                                                          
                                                 
FALLBACK_VRAM_MB = 6144        

               
WINDOW_SIZE = "1280x768"
SIDEBAR_WIDTH = 450
RIGHT_SIDEBAR_WIDTH = 300
PREVIEW_SIZE = (600, 400)

                 
# Colors & Aesthetics (Premium Dark Theme)
THEME_PRIMARY = "#3498db"
THEME_ACCENT = "#f39c12"
THEME_BG_DEEP = "#0d1117"
THEME_BG_PANEL = "#161b22"
THEME_TEXT_BOLD = "#ffffff"   # Pure White for best contrast
THEME_TEXT_MUTED = "#cfd9e5"  # Light Blueish Gray for readability
THEME_BORDER = "#444c56"

                                
                                                                                     
FREEU_MAX_VALUES = {
    "s1": 0.6, "s2": 0.4,
    "b1": 1.1, "b2": 1.2
}
FREEU_DEFAULT_INTENSITY = 0.5
