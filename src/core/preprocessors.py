import torch
import numpy as np
import cv2
from PIL import Image, ImageOps
from transformers import pipeline

class ImagePreprocessors:
    """Handles image preprocessing for ControlNet (Depth, Canny, Segmentation)."""
    def __init__(self, device, dtype):
        self.device = device
        self.dtype = dtype
        self.depth_est = None
        self.seg_processor = None
        self.seg_model = None

    def preprocess_segmentation(self, image, MODELS_DIR):
        """
        Runs OneFormer semantic segmentation.
        Returns: (colored_pil_image, auto_tags_string)
        - colored_pil_image: ADE20K palette colored segmentation map (PIL Image)
        - auto_tags_string: comma-separated detected object names
        """
        model_path = MODELS_DIR / "solid_models" / "oneformer"

        # Lazy load model (first call only)
        if self.seg_model is None:
            print(f"🔄 Loading OneFormer Segmentation Model: {model_path}")
            from transformers import OneFormerProcessor, OneFormerForUniversalSegmentation
            self.seg_processor = OneFormerProcessor.from_pretrained(str(model_path))
            self.seg_model = OneFormerForUniversalSegmentation.from_pretrained(str(model_path))
            self.seg_model.to(self.device)
            self.seg_model.eval()

        # Run semantic segmentation
        inputs = self.seg_processor(images=image, task_inputs=["semantic"], return_tensors="pt")
        inputs = {k: v.to(self.device) if hasattr(v, 'to') else v for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.seg_model(**inputs)
        
        seg_map = self.seg_processor.post_process_semantic_segmentation(
            outputs, target_sizes=[image.size[::-1]]
        )[0].cpu().numpy()

        # Extract text tags from detected labels
        unique_labels = np.unique(seg_map)
        id2label = self.seg_model.config.id2label
        tags = []
        for label_id in unique_labels:
            label_name = id2label.get(int(label_id), None)
            if label_name and label_name.lower() not in ("", "wall", "floor", "ceiling"):
                tags.append(label_name)
        auto_tags = ", ".join(tags) if tags else ""

        # Build colored segmentation map (ADE20K 150-color palette)
        colored = self._apply_ade20k_palette(seg_map)

        return colored, auto_tags

    @staticmethod
    def _apply_ade20k_palette(seg_map):
        """Applies the standard ADE20K 150-color palette to a segmentation map."""
        # ADE20K standard palette (150 classes)
        palette = np.array([
            [120,120,120],[180,120,120],[6,230,230],[80,50,50],[4,200,3],
            [120,120,80],[140,140,140],[204,5,255],[230,230,230],[4,250,7],
            [224,5,255],[235,255,7],[150,5,61],[120,120,70],[8,255,51],
            [255,6,82],[143,255,140],[204,255,4],[255,51,7],[204,70,3],
            [0,102,200],[61,230,250],[255,6,51],[11,102,255],[255,7,71],
            [255,9,224],[9,7,230],[220,220,220],[255,9,92],[112,9,255],
            [8,255,214],[7,255,224],[255,184,6],[10,255,71],[255,41,10],
            [7,255,255],[224,255,8],[102,8,255],[255,61,6],[255,194,7],
            [255,122,8],[0,255,20],[255,8,41],[255,5,153],[6,51,255],
            [235,12,255],[160,150,20],[0,163,255],[140,140,140],[250,10,15],
            [20,255,0],[31,255,0],[255,31,0],[255,224,0],[153,255,0],
            [0,0,255],[255,71,0],[0,235,255],[0,173,255],[31,0,255],
            [11,200,200],[255,82,0],[0,255,245],[0,61,255],[0,255,112],
            [0,255,133],[255,0,0],[255,163,0],[255,102,0],[194,255,0],
            [0,143,255],[51,255,0],[0,82,255],[0,255,41],[0,255,173],
            [10,0,255],[173,255,0],[0,255,153],[255,92,0],[255,0,255],
            [255,0,245],[255,0,102],[255,173,0],[255,0,20],[255,184,184],
            [0,31,255],[0,255,61],[0,71,255],[255,0,204],[0,255,194],
            [0,255,82],[0,10,255],[0,112,255],[51,0,255],[0,194,255],
            [0,122,255],[0,255,163],[255,153,0],[0,255,10],[255,112,0],
            [143,255,0],[82,0,255],[163,255,0],[255,235,0],[8,184,170],
            [133,0,255],[0,255,92],[184,0,255],[255,0,31],[0,184,255],
            [0,214,255],[255,0,112],[92,255,0],[0,224,255],[112,224,255],
            [70,184,160],[163,0,255],[153,0,255],[71,255,0],[255,0,163],
            [255,204,0],[255,0,143],[0,255,235],[133,255,0],[255,0,235],
            [245,0,255],[255,0,122],[255,245,0],[10,190,212],[214,255,0],
            [0,204,255],[20,0,255],[255,255,0],[0,153,255],[0,41,255],
            [0,255,204],[41,0,255],[41,255,0],[173,0,255],[0,245,255],
            [71,0,255],[122,0,255],[0,255,184],[0,92,255],[184,255,0],
            [0,133,255],[255,214,0],[25,194,194],[102,255,0],[92,0,255],
        ], dtype=np.uint8)

        h, w = seg_map.shape
        colored = np.zeros((h, w, 3), dtype=np.uint8)
        for label_id in np.unique(seg_map):
            idx = int(label_id) % len(palette)
            colored[seg_map == label_id] = palette[idx]

        return Image.fromarray(colored)

    def preprocess_depth(self, image, MODELS_DIR):
        if self.depth_est is None:
            local_path = MODELS_DIR / "solid_models" / "MiDaS-dpt-large-fp16"
            self.depth_est = pipeline("depth-estimation", model=str(local_path), device=self.device, dtype=torch.float32)
            
        inputs = self.depth_est.image_processor(images=image, return_tensors="pt").to(
            device=self.device, 
            dtype=torch.float32
        )
        with torch.no_grad():
            outputs = self.depth_est.model(**inputs)
            predicted_depth = outputs.predicted_depth
            
        prediction = torch.nn.functional.interpolate(
            predicted_depth.unsqueeze(1),
            size=image.size[::-1],
            mode="bicubic",
            align_corners=False,
        )
        
        depth_min = prediction.min()
        depth_max = prediction.max()
        depth_map = (prediction - depth_min) / (depth_max - depth_min)
        
        return depth_map.repeat(1, 3, 1, 1).to(dtype=self.dtype)

    def preprocess_canny(self, image, low_threshold=100, high_threshold=200, auto_mode=False):
        image_np = np.array(image)
        if auto_mode:
            v = np.median(image_np)
            low_threshold = int(max(0, (low_threshold / 100.0) * v))
            high_threshold = int(min(255, (high_threshold / 100.0) * v))
            
        edges = cv2.Canny(image_np, low_threshold, high_threshold)
        edges_3d = np.concatenate([edges[:, :, None]] * 3, axis=2)
        edges_tensor = torch.from_numpy(edges_3d).to(dtype=self.dtype) / 255.0
        
        return edges_tensor.permute(2, 0, 1).unsqueeze(0).to(device=self.device)
