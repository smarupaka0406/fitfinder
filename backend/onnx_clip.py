import onnxruntime as ort
import numpy as np
from PIL import Image
import threading

# Singleton ONNX session for efficiency
_onnx_session = None
_onnx_lock = threading.Lock()

ONNX_MODEL_PATH = "clip-vit-base-patch32-image.onnx"  # Update path if needed

CLIP_IMAGE_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
CLIP_IMAGE_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)


def get_onnx_clip_image_encoder():
    global _onnx_session
    with _onnx_lock:
        if _onnx_session is None:
            _onnx_session = ort.InferenceSession(ONNX_MODEL_PATH)
        return _onnx_session

def preprocess_image(image_path, image_size=224):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((image_size, image_size))
    img_np = np.array(image).astype(np.float32) / 255.0
    img_np = (img_np - CLIP_IMAGE_MEAN) / CLIP_IMAGE_STD
    img_np = np.transpose(img_np, (2, 0, 1))  # HWC to CHW
    img_np = np.expand_dims(img_np, 0)  # Add batch dim
    # Keep ONNX input as float32 to match tensor(float) model input type.
    return np.ascontiguousarray(img_np, dtype=np.float32)

def get_image_embedding(image_path):
    session = get_onnx_clip_image_encoder()
    img = preprocess_image(image_path)
    inputs = {session.get_inputs()[0].name: img}
    embedding = session.run(None, inputs)[0]
    norm = np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding / norm

def cosine_similarity(vec1, vec2):
    left = np.asarray(vec1, dtype=np.float32).reshape(-1)
    right = np.asarray(vec2, dtype=np.float32).reshape(-1)

    if left.size == 0 or right.size == 0 or left.size != right.size:
        raise ValueError("Embeddings must be non-empty and the same length")

    denom = np.linalg.norm(left) * np.linalg.norm(right)
    if denom == 0:
        return 0.0
    return float(np.dot(left, right) / denom)
