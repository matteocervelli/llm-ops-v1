import base64
import os
from pathlib import Path
from typing import Any

import httpx


class FabricaVisionClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.getenv("FABRICA_URL", "http://localhost:8765")

    async def analyze_image(self, image_path: Path, prompt: str) -> dict[str, Any]:
        payload = {
            "prompt": prompt,
            "image_base64": base64.b64encode(image_path.read_bytes()).decode("utf-8"),
            "filename": image_path.name,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/analyze", json=payload)
            response.raise_for_status()
            return response.json()
