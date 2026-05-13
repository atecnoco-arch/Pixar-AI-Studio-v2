\
\
\
\
\
   
import cv2
import numpy as np
from PIL import Image
import threading

from collections import OrderedDict

class VisualProcessor:
    def __init__(self, cache_size=8):
        self._cache = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()

    def clear_cache(self):
        with self._lock:
            self._cache.clear()
            return True

    def set_cache_size(self, size):
        with self._lock:
            self._cache_size = size
            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
            return True

    def get_canny_preview(self, image_path, low_threshold, high_threshold, auto=False, size=(260, 200)):
\
\
           
        import os
        if not image_path or not os.path.exists(image_path):
            return None, "No Image"

                                         
        cache_key = f"{image_path}_{low_threshold}_{high_threshold}_{auto}_{size}"
        
        with self._lock:
            if cache_key in self._cache:
                                                                      
                self._cache.move_to_end(cache_key)
                return self._cache[cache_key], "Cached"

            try:
                           
                img = Image.open(image_path)
                img_np = np.array(img)
                
                                                     
                if len(img_np.shape) == 3:
                    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_np

                if auto:
                    v = np.median(gray)
                    low = int(max(0, (low_threshold / 100.0) * v))
                    high = int(min(255, (high_threshold / 100.0) * v))
                else:
                    low = low_threshold
                    high = high_threshold

                               
                edges = cv2.Canny(gray, low, high)
                
                                                         
                edge_img = Image.fromarray(edges)
                edge_img.thumbnail(size)
                
                                                                      
                self._cache[cache_key] = edge_img
                if len(self._cache) > self._cache_size:
                    self._cache.popitem(last=False)                              
                
                return edge_img, f"Edges (L:{low} H:{high})"
            except Exception as e:
                return None, f"Error: {str(e)}"
