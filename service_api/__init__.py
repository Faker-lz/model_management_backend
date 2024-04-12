from .gpu_status_api import gpu_api_router
from .models_api import model_api_router

__all__ = [
    "gpu_api_router",
    "model_api_router",
]