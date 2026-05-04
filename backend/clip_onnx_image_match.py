import onnxruntime as ort
import numpy as np
from PIL import Image

# Path to your ONNX CLIP image encoder model
def load_clip_onnx_model(model_path):
    return ort.InferenceSession(model_path)

def preprocess_image(image_path, image_size=224):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((image_size, image_size))
    img_np = np.array(image).astype(np.float32) / 255.0
    # Normalize using CLIP mean/std
    mean = np.array([0.48145466, 0.4578275, 0.40821073])
    std = np.array([0.26862954, 0.26130258, 0.27577711])
    img_np = (img_np - mean) / std
    img_np = np.transpose(img_np, (2, 0, 1))  # HWC to CHW
    img_np = np.expand_dims(img_np, 0)  # Add batch dim
    return img_np

def get_image_embedding(model, image_array):
    inputs = {model.get_inputs()[0].name: image_array}
    embedding = model.run(None, inputs)[0]
    # Normalize the embedding
    norm = np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding / norm

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2.T)

# Example usage:
# model = load_clip_onnx_model("clip-vit-base-patch32-image-encoder.onnx")
# img1 = preprocess_image("image1.jpg")
# img2 = preprocess_image("image2.jpg")
# emb1 = get_image_embedding(model, img1)
# emb2 = get_image_embedding(model, img2)
# similarity = cosine_similarity(emb1, emb2)
# print("Similarity:", similarity)
