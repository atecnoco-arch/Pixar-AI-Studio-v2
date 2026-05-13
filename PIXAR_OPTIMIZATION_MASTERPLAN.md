# طرح جامع و قطعی بهینه‌سازی استودیو پیکسار (Pixar AI Studio Masterplan)
**هدف:** رسیدن به حداکثر کیفیت (شاهکار) و افزایش سرعت تا ۳ برابر در محیط سخت‌افزاری محدود (۶ گیگابایت VRAM).

این سند به گونه‌ای تنظیم شده که هر نسخه از هوش مصنوعی (Antigravity) با خواندن آن، دقیقاً بداند چه کتابخانه‌هایی نصب کند، چه مدل‌هایی را جایگزین کند و ساختار کدهای پایتون را چگونه تغییر دهد. شما می‌توانید این فایل را به همراه پوشه پروژه به هر کامپیوتر دیگری منتقل کنید و به هوش مصنوعی آن کامپیوتر بگویید "طبق این مسترپلن عمل کن".

## فاز ۱: ارتقای پیش‌نیازها و کتابخانه‌ها (Dependencies)
برای اجرای تکنیک‌های جدید، هوش مصنوعی ابتدا باید این کتابخانه‌ها را در محیط مجازی (`.venv`) نصب یا آپدیت کند:
1. `bitsandbytes`: برای فشرده‌سازی ۴-بیتی (NF4).
2. `xformers`: برای مدیریت بهینه حافظه در محاسبات Attention.
3. `DeepCache`: برای جهش در مراحل پردازش و دو برابر کردن سرعت خالص.
*(دستور: `pip install bitsandbytes xformers DeepCache`)*

## فاز ۲: معماری جدید مدل‌ها (Model Replacements)
مدل‌های فعلی باید با نسخه‌های بهینه‌تر جایگزین شوند:
1. **هسته اصلی (UNet):** مهاجرت از SDXL استاندارد یا LCM به **SDXL-Lightning** (مانند Juggernaut-Lightning). این مدل‌ها در ۴ الی ۸ قدم بالاترین کیفیت را می‌دهند و مات نمی‌شوند.
2. **شبکه کنترل (ControlNet):** مهاجرت از `ControlNet-Depth` به **`ControlNet-Tile`**. (مدل Tile بافت‌ها، آجرها و پیکسل‌های تصویر اولیه را بسیار دقیق‌تر از Depth حفظ می‌کند).
3. **زمان‌بند (Scheduler):** حذف `LCMScheduler` و استفاده از `EulerDiscreteScheduler` یا `TCDScheduler`.

## فاز ۳: تغییرات ساختاری در کدهای هسته (`src/core/renderer.py`)
هوش مصنوعی باید تغییرات زیر را دقیقاً پیاده‌سازی کند:

### ۱. کوانتیزاسیون ۴-بیتی (NF4 UNet)
در زمان لود کردن پایپ‌لاین (`StableDiffusionXLControlNetImg2ImgPipeline`)، باید `UNet` با تنظیمات زیر لود شود:
```python
from transformers import BitsAndBytesConfig
import torch

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)
# لود کردن UNet جداگانه با کوانتیزاسیون و پاس دادن آن به Pipeline
```
*اثر:* کاهش حجم UNet از ۵ گیگابایت به ۱.۵ گیگابایت.

### ۲. حذف پینگ‌پونگ رم و گرافیک (Memory Hook Refactoring)
به دلیل اینکه حجم UNet اکنون ۱.۵ گیگابایت شده است، دیگر نیازی به جابجایی مداوم (CPU <-> GPU) نیست.
- UNet، ControlNet، و IP-Adapter می‌توانند همزمان و به طور دائم در VRAM (`cuda`) بمانند (King).
- فقط `Text Encoders` و `VAE` باید در زمان عدم استفاده به CPU منتقل شوند.
*اثر:* حذف کامل گلوگاه پهنای باند PCIe (PCIe Bottleneck) و افزایش چشمگیر سرعت.

### ۳. فعال‌سازی xFormers
باید بلافاصله پس از لود پایپ‌لاین، دستور زیر اجرا شود:
```python
self.pipe.enable_xformers_memory_efficient_attention()
```
*اثر:* کاهش مصرف VRAM در حین عملیات پردازش تصویر.

### ۴. ادغام DeepCache
هوش مصنوعی باید کش عمیق را به شکل زیر به پایپ‌لاین متصل کند:
```python
from DeepCache import DeepCacheSDHelper
helper = DeepCacheSDHelper(pipe=self.pipe)
helper.set_params(cache_interval=2, cache_branch_id=0)
helper.enable()
```
*اثر:* با کش کردن لایه‌ها در قدم‌های زوج، زمان رندر نصف می‌شود.

## فاز ۴: تغییرات رابط کاربری (`src/gui.py`)
1. اضافه شدن سوییچ **"NF4 Turbo Mode"** برای کنترل فعال‌سازی حالت ۴-بیتی.
2. اضافه شدن سوییچ **"DeepCache Acceleration"** برای روشن/خاموش کردن کش.
3. حذف زمان‌بند‌های منسوخ شده و سازگار کردن اسلایدر Guidance Scale با مدل‌های Lightning (قفل کردن روی اعداد پایین مثل ۱.۵).

## فاز ۵: تست و اعتبارسنجی (Validation)
پس از پیاده‌سازی، هوش مصنوعی باید:
1. ترمینال را مانیتور کند تا هیچ‌گونه خطای `Out of Memory` رخ ندهد.
2. لاگ انتقال (Transfer Logs) را چک کند تا مطمئن شود UNet بی‌دلیل به CPU منتقل نمی‌شود و در GPU مقیم است.
3. یک تصویر تست (تبدیل بلوک‌های ماینکرافت به شاهکار انیمه) رندر بگیرد و تأیید کند که بافت‌ها و رنگ‌ها (Cel Shading) به لطف مدل Tile و NF4 به درستی حفظ شده و ارتقا یافته‌اند.
