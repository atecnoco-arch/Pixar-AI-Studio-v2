import torch
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from spandrel import ModelLoader

class PixarUpscaler:
    def __init__(self, device="cuda", model_name="RealESRGAN_x4plus.pth"):
        self.device = torch.device(device)
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.model_path = self.base_dir / "models" / "upscalers" / model_name
        self.model = None

    def load_model(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"مدل Upscaler در مسیر پیدا نشد: {self.model_path}")
        
        print(f"📦 در حال بارگذاری مدل Upscaler از: {self.model_path}")
        model_loader = ModelLoader()
        self.model = model_loader.load_from_file(str(self.model_path))
        self.model.to(self.device).eval()
                                                 
        if hasattr(self.model, 'half'):
            self.model.half()
        print("✅ مدل Upscaler با موفقیت بارگذاری و در حافظه گرافیک قرار گرفت.")

    def unload(self):
        if self.model is not None:
            self.model.to("cpu")
            del self.model
            self.model = None
            torch.cuda.empty_cache()
            print("🧹 مدل Upscaler از حافظه گرافیک آزاد شد.")

    def process_image(self, pil_img: Image.Image, target_scale: int = 2) -> Image.Image:
\
\
\
           
        if self.model is None:
            self.load_model()
            
        print(f"🔍 در حال ارتقای کیفیت تصویر (مدل 4x با خروجی نهایی {target_scale}x)...")
                                                        
        img_np = np.array(pil_img)
        if img_np.ndim == 2:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB)
        elif img_np.shape[2] == 4:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
            
                                                       
        img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        img_tensor = img_tensor.to(self.device)
        if hasattr(self.model, 'half'):
             img_tensor = img_tensor.half()
        
        with torch.no_grad():
            b, c, h, w = img_tensor.shape
            scale_factor = 4 # RealESRGAN_x4plus default
            out_h, out_w = h * scale_factor, w * scale_factor
            
            # تخصیص حافظه در کارت گرافیک (VRAM) برای سرعت حداکثری
            dtype_to_use = img_tensor.dtype
            output = torch.zeros((b, c, out_h, out_w), device=self.device, dtype=dtype_to_use)
            
            tile_size = 512
            overlap = 32
            

            
            for y in range(0, h, tile_size - overlap):
                for x in range(0, w, tile_size - overlap):
                    y_start = max(0, y)
                    x_start = max(0, x)
                    y_end = min(h, y_start + tile_size)
                    x_end = min(w, x_start + tile_size)
                    
                    # در صورتی که تکه آخر کوچکتر از tile_size باشد، از عقب جبران می‌کنیم
                    if y_end - y_start < tile_size and h >= tile_size: y_start = y_end - tile_size
                    if x_end - x_start < tile_size and w >= tile_size: x_start = x_end - tile_size
                    
                    tile = img_tensor[:, :, y_start:y_end, x_start:x_end]
                    # پردازش روی GPU و نگه داشتن خروجی در GPU
                    tile_out = self.model(tile)
                    
                    oy, oy_end = y_start * scale_factor, y_end * scale_factor
                    ox, ox_end = x_start * scale_factor, x_end * scale_factor
                    
                    # جایگزینی مستقیم روی GPU (بسیار سریع‌تر از کپی روی RAM)
                    output[:, :, oy:oy_end, ox:ox_end] = tile_out
            
                                        
        output = output.squeeze(0).permute(1, 2, 0).clamp(0, 1).float().cpu().numpy()
        output_np = (output * 255.0).round().astype(np.uint8)
        
                                               
        del img_tensor
        
        upscaled_img = Image.fromarray(output_np)
        
                                                                                    
                                                                       
        target_w = pil_img.width * target_scale
        target_h = pil_img.height * target_scale
        
        if upscaled_img.width > target_w:
            result_img = upscaled_img.resize((target_w, target_h), Image.LANCZOS)
        else:
            result_img = upscaled_img

        print(f"✅ ارتقای کیفیت انجام شد: ابعاد نهایی -> {result_img.width}x{result_img.height}")
        return result_img
