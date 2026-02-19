"""
SentinelAI — Image Analyzer Service

Deepfake / AI-generated image detection pipeline:
1. Preprocess image (resize, normalize)
2. Run through a CNN-based classifier
3. Return deepfake probability

Uses a lightweight CNN architecture as a placeholder —
in production, swap in a fine-tuned EfficientNet or similar model.
"""

import io
import logging
import numpy as np
from typing import Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)

# Lazy-loaded model
_image_model = None
_device = None


def _build_simple_cnn():
    """
    Build a simple CNN for deepfake classification.
    This serves as a placeholder — replace with a pre-trained model
    (e.g. EfficientNet fine-tuned on FaceForensics++) for production.
    """
    try:
        import torch
        import torch.nn as nn

        class DeepfakeCNN(nn.Module):
            def __init__(self):
                super().__init__()
                self.features = nn.Sequential(
                    nn.Conv2d(3, 32, 3, padding=1),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    nn.Conv2d(32, 64, 3, padding=1),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    nn.Conv2d(64, 128, 3, padding=1),
                    nn.ReLU(),
                    nn.AdaptiveAvgPool2d(4),
                )
                self.classifier = nn.Sequential(
                    nn.Flatten(),
                    nn.Linear(128 * 4 * 4, 256),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(256, 2),
                )

            def forward(self, x):
                x = self.features(x)
                x = self.classifier(x)
                return x

        model = DeepfakeCNN()
        model.eval()
        return model

    except ImportError:
        logger.warning("PyTorch not available — image analysis will use heuristic mode")
        return None


def _load_model():
    """Load or initialise the image classification model."""
    global _image_model, _device
    if _image_model is None:
        try:
            import torch
            _device = torch.device("cpu")
            _image_model = _build_simple_cnn()
            if _image_model:
                _image_model.to(_device)
                logger.info("Image analysis model initialised (placeholder CNN)")
        except ImportError:
            _image_model = None
    return _image_model


def preprocess_image(image_bytes: bytes) -> Any:
    """
    Preprocess image for CNN inference.
    - Resize to 224x224
    - Normalise pixel values
    - Convert to tensor
    """
    try:
        import torch
        import torchvision.transforms as T

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        tensor = transform(image).unsqueeze(0)  # Add batch dimension
        return tensor

    except ImportError:
        # Return PIL image for heuristic processing
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return image


def _heuristic_image_analysis(image_bytes: bytes) -> Dict[str, float]:
    """
    Heuristic-based image analysis for when PyTorch is unavailable.
    
    Checks statistical properties of the image:
    - Uniform noise patterns (common in GAN outputs)
    - Unusual colour distributions
    - Compression artefact consistency
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = np.array(image, dtype=np.float32)

    # Check channel statistics
    channel_stds = [pixels[:, :, c].std() for c in range(3)]
    avg_std = np.mean(channel_stds)

    # Check for suspiciously uniform noise
    high_freq = np.abs(np.diff(pixels, axis=0)).mean()

    # GAN images often have lower high-frequency noise
    score = 0.0
    if avg_std < 40:
        score += 0.3
    if high_freq < 10:
        score += 0.3
    elif high_freq < 20:
        score += 0.15

    # Check symmetry (GANs sometimes produce symmetric artefacts)
    h, w = pixels.shape[:2]
    if w > 10:
        left = pixels[:, :w // 4, :]
        right = np.flip(pixels[:, -w // 4:, :], axis=1)
        min_w = min(left.shape[1], right.shape[1])
        symmetry = np.mean(np.abs(left[:, :min_w] - right[:, :min_w]))
        if symmetry < 15:
            score += 0.2

    return {"deepfake_probability": min(round(score + 0.1, 4), 0.95)}


def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Full image analysis pipeline.
    
    Returns:
    - deepfake_probability: float [0,1]
    - analysis_method: 'cnn' or 'heuristic'
    """
    model = _load_model()

    if model is not None:
        try:
            import torch
            import torch.nn.functional as F

            tensor = preprocess_image(image_bytes)
            if not isinstance(tensor, torch.Tensor):
                raise ValueError("Preprocessing did not return a tensor")

            with torch.no_grad():
                logits = model(tensor)
                probs = F.softmax(logits, dim=1)
                # Class 1 = deepfake / AI-generated
                deepfake_prob = probs[0][1].item()

            return {
                "deepfake_probability": round(deepfake_prob, 4),
                "analysis_method": "cnn",
            }

        except Exception as e:
            logger.error(f"CNN inference failed: {e}")
            result = _heuristic_image_analysis(image_bytes)
            result["analysis_method"] = "heuristic_fallback"
            return result
    else:
        result = _heuristic_image_analysis(image_bytes)
        result["analysis_method"] = "heuristic"
        return result
