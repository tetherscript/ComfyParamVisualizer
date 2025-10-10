# custom_nodes/select_image_by_index.py

import torch

class SelectImageByIndex:
    """
    Select a single image from a batch (IMAGE) by zero-based index.
    If the selected index is out of range, outputs nothing.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "selected_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1_000_000,
                    "step": 1
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "select"
    CATEGORY = "utils"

    def select(self, images: torch.Tensor, selected_index: int):
        # Validate
        if not isinstance(images, torch.Tensor):
            raise TypeError("images must be a torch.Tensor with shape [B, C, H, W].")
        if images.ndim != 4:
            raise ValueError(f"Expected shape [B, C, H, W], got {tuple(images.shape)}.")

        batch_size = int(images.shape[0])
        if batch_size == 0:
            return ()

        # Out-of-range? -> Do nothing
        if selected_index < 0 or selected_index >= batch_size:
            return ()

        # Slice one image, preserving batch dimension
        out = images[selected_index:selected_index + 1].contiguous()
        return (out,)


NODE_CLASS_MAPPINGS = {
    "SelectImageByIndex": SelectImageByIndex,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SelectImageByIndex": "Select Image By Index",
}
