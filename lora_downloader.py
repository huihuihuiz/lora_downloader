import os
import requests
import folder_paths
from server import PromptServer
from aiohttp import web
import urllib.parse

class LoraDownloader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lora_name": ("STRING", {"default": "example.safetensors"}),
                "download_url": ("STRING", {"default": "https://example.com/lora.safetensors"}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "download_lora"
    OUTPUT_NODE = True
    CATEGORY = "utils"

    def download_lora(self, lora_name, download_url):
        # This function will be called when the node is executed
        # The actual download will happen through the HTTP endpoint
        return ()

# Create an HTTP route for downloading LoRA files
@PromptServer.instance.routes.post("/lora_downloader/download")
async def download_lora_endpoint(request):
    try:
        data = await request.json()
        lora_name = data.get("lora_name", "")
        download_url = data.get("download_url", "")
        
        if not lora_name or not download_url:
            return web.json_response({"error": "Missing lora_name or download_url"}, status=400)
        
        # Get the LoRA directory
        lora_directory = folder_paths.get_folder_paths("loras")[0]
        
        # Create full file path
        file_path = os.path.join(lora_directory, lora_name)
        
        # Check if file already exists
        if os.path.exists(file_path):
            return web.json_response({"message": f"File {lora_name} already exists"}, status=200)
        
        # Download the file
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # Save the file
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return web.json_response({"message": f"Successfully downloaded {lora_name}"}, status=200)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# Create an HTTP route for listing available LoRA files
@PromptServer.instance.routes.get("/lora_downloader/list")
async def list_loras_endpoint(request):
    try:
        lora_directory = folder_paths.get_folder_paths("loras")[0]
        lora_files = []
        
        if os.path.exists(lora_directory):
            # Recursively walk through all subdirectories
            for root, dirs, files in os.walk(lora_directory):
                for file in files:
                    if file.endswith(('.safetensors', '.ckpt', '.pt')):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        # Get relative path from lora_directory
                        relative_path = os.path.relpath(file_path, lora_directory)
                        lora_files.append({
                            "name": relative_path,
                            "size": file_size
                        })
        
        return web.json_response({"loras": lora_files}, status=200)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# Serve static files for the web interface
@PromptServer.instance.routes.get("/lora_downloader")
async def serve_lora_downloader_page(request):
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        web_dir = os.path.join(script_dir, "web")
        index_file = os.path.join(web_dir, "index.html")
        
        # Serve the index.html file
        return web.FileResponse(index_file)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# Serve static assets
@PromptServer.instance.routes.get("/lora_downloader/{filename}")
async def serve_static_assets(request):
    try:
        filename = request.match_info["filename"]
        script_dir = os.path.dirname(os.path.realpath(__file__))
        web_dir = os.path.join(script_dir, "web")
        file_path = os.path.join(web_dir, filename)
        
        # Security check to prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(web_dir)):
            return web.json_response({"error": "Forbidden"}, status=403)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return web.json_response({"error": "File not found"}, status=404)
        
        return web.FileResponse(file_path)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# Download LoRA file from server to local
@PromptServer.instance.routes.get("/lora_downloader/download_file/{filename:.+}")
async def download_lora_file(request):
    try:
        filename = urllib.parse.unquote(request.match_info["filename"])
        lora_directory = folder_paths.get_folder_paths("loras")[0]
        file_path = os.path.join(lora_directory, filename)
        
        # Security check to prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(lora_directory)):
            return web.json_response({"error": "Forbidden"}, status=403)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return web.json_response({"error": "File not found"}, status=404)
        
        # Get just the filename without path for download
        download_filename = os.path.basename(file_path)
        
        # Set response headers for file download
        return web.FileResponse(
            file_path,
            headers={
                'Content-Disposition': f'attachment; filename="{download_filename}"'
            }
        )
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# Node class mappings
NODE_CLASS_MAPPINGS = {
    "LoraDownloader": LoraDownloader
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraDownloader": "LoRA Downloader"
}
