import json
import uuid
import asyncio
import aiohttp
from typing import Optional, Callable
from pathlib import Path


class ComfyUIClient:
    """Client for interacting with ComfyUI API"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.client_id = str(uuid.uuid4())

    async def is_available(self) -> bool:
        """Check if ComfyUI server is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/system_stats", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def queue_prompt(self, workflow: dict) -> str:
        """Queue a workflow for execution and return prompt_id"""
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/prompt",
                json=payload
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise RuntimeError(f"Failed to queue prompt: {error}")
                result = await resp.json()
                return result["prompt_id"]

    async def get_history(self, prompt_id: str) -> Optional[dict]:
        """Get execution history for a prompt"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/history/{prompt_id}") as resp:
                if resp.status != 200:
                    return None
                history = await resp.json()
                return history.get(prompt_id)

    async def wait_for_completion(
        self,
        prompt_id: str,
        progress_callback: Optional[Callable] = None,
        timeout: int = 3600
    ) -> dict:
        """Wait for workflow execution to complete using WebSocket"""
        ws_url = f"ws://{self.host}:{self.port}/ws?clientId={self.client_id}"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                start_time = asyncio.get_event_loop().time()

                async for msg in ws:
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        raise TimeoutError("Workflow execution timed out")

                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        msg_type = data.get("type")

                        if msg_type == "progress":
                            progress_data = data.get("data", {})
                            current = progress_data.get("value", 0)
                            total = progress_data.get("max", 1)
                            if progress_callback:
                                progress_callback(current / total if total > 0 else 0)

                        elif msg_type == "executing":
                            exec_data = data.get("data", {})
                            if exec_data.get("prompt_id") == prompt_id:
                                if exec_data.get("node") is None:
                                    # Execution completed
                                    break

                        elif msg_type == "execution_error":
                            error_data = data.get("data", {})
                            raise RuntimeError(f"Execution error: {error_data}")

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        raise RuntimeError(f"WebSocket error: {ws.exception()}")

        # Get final result from history
        history = await self.get_history(prompt_id)
        if not history:
            raise RuntimeError("Failed to get execution history")

        return history

    async def get_output_video(self, history: dict) -> Optional[str]:
        """Extract output video path from execution history"""
        outputs = history.get("outputs", {})

        for node_id, node_output in outputs.items():
            if "gifs" in node_output:
                for gif in node_output["gifs"]:
                    filename = gif.get("filename")
                    subfolder = gif.get("subfolder", "")
                    if filename:
                        return f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type=output"
            if "videos" in node_output:
                for video in node_output["videos"]:
                    filename = video.get("filename")
                    subfolder = video.get("subfolder", "")
                    if filename:
                        return f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type=output"

        return None

    async def download_video(self, video_url: str, output_path: Path) -> str:
        """Download video from ComfyUI to local path"""
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Failed to download video: {resp.status}")

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)

        return str(output_path)


# Global client instance
comfyui_client = ComfyUIClient()
