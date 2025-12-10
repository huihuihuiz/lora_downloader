import os
import requests
import folder_paths
from server import PromptServer
from aiohttp import web
import urllib.parse

# ---------------------------------------
# Secure path join helper
# ---------------------------------------
def safe_join(base_dir, user_path):
    base = os.path.abspath(base_dir)
    final_path = os.path.abspath(os.path.join(base, user_path))

    # Ensure path is strictly inside base directory
    if os.path.commonpath([base, final_path]) != base:
        raise ValueError("Illegal path")

    return final_path


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
        # Real download handled via HTTP endpoint
        return ()


# ---------------------------------------
# Download LoRA from URL -> save to server
# ---------------------------------------
@PromptServer.instance.routes.post("/lora_downloader/download")
async def download_lora_endpoint(request):
    try:
        data = await request.json()

        lora_name = data.get("lora_name", "").strip()
        download_url = data.get("download_url", "").strip()

        if not lora_name or not download_url:
            return web.json_response(
                {"error": "Missing lora_name or download_url"}, status=400
            )

        lora_directory = folder_paths.get_folder_paths("loras")[0]

        try:
            file_path = safe_join(lora_directory, lora_name)
        except ValueError:
            return web.json_response({"error": "Illegal file path"}, status=403)

        # Create subfolders if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if os.path.exists(file_path):
            return web.json_response(
                {"message": f"File {lora_name} already exists"}, status=200
            )

        # Download file
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return web.json_response(
            {"message": f"Successfully downloaded {lora_name}"}, status=200
        )

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ---------------------------------------
# List all existing LoRA files
# ---------------------------------------
@PromptServer.instance.routes.get("/lora_downloader/list")
async def list_loras_endpoint(request):
    try:
        lora_directory = folder_paths.get_folder_paths("loras")[0]
        lora_files = []

        if os.path.exists(lora_directory):
            for root, dirs, files in os.walk(lora_directory):
                for file in files:
                    if file.endswith((".safetensors", ".ckpt", ".pt")):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, lora_directory)
                        lora_files.append(
                            {
                                "name": relative_path,
                                "size": os.path.getsize(file_path),
                            }
                        )

        return web.json_response({"loras": lora_files}, status=200)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ---------------------------------------
# Web UI (HTML embedded)
# ---------------------------------------
@PromptServer.instance.routes.get("/lora_downloader")
async def serve_lora_downloader_page(request):
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>ComfyUI LoRA 下载器</title>
<style>
body{font-family:Arial, sans-serif;max-width:1000px;margin:0 auto;background:#f5f5f5;padding:20px;}
.container{background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.1);}
h1{text-align:center;}
input,button{padding:10px;margin-top:5px;width:100%;}
button{cursor:pointer;}
.lora-item{border-bottom:1px solid #eee;padding:6px 0;}
.download-btn{margin-left:10px;}
</style>
</head>
<body>
<div class="container">
<h1>ComfyUI LoRA 下载器</h1>

<form id="downloadForm">
<input id="loraName" placeholder="example.safetensors" required>
<input id="downloadUrl" type="url" placeholder="https://example.com/example.safetensors" required>
<button type="submit">下载 LoRA</button>
</form>

<div id="result"></div>

<h3>已有 LoRA</h3>
<button id="refreshBtn">刷新列表</button>
<button id="downloadAllBtn">全部下载</button>
<div id="loraList"></div>
<div id="progress"></div>
</div>

<script>
const baseUrl = window.location.origin;
let allLoras=[];

async function loadLoraList(){
    const r=await fetch(`${baseUrl}/lora_downloader/list`);
    const d=await r.json();
    let html='';
    allLoras=d.loras||[];
    allLoras.forEach(l=>{
        const mb=(l.size/1024/1024).toFixed(2);
        html+=`<div class="lora-item">${l.name} (${mb}MB)
        <button class="download-btn" onclick="downloadLora('${encodeURIComponent(l.name)}')">下载</button></div>`;
    });
    document.getElementById('loraList').innerHTML=html||'暂无文件';
}

function downloadLora(name){
    const link=document.createElement('a');
    link.href=`${baseUrl}/lora_downloader/download_file/${name}`;
    link.download=name.split('/').pop();
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

document.getElementById('downloadForm').addEventListener('submit',async e=>{
    e.preventDefault();
    const data={
        lora_name:loraName.value,
        download_url:downloadUrl.value
    };
    const r=await fetch(`${baseUrl}/lora_downloader/download`,{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(data)
    });
    const d=await r.json();
    result.textContent=d.message||d.error;
    loadLoraList();
});

document.getElementById('refreshBtn').onclick=loadLoraList;

document.getElementById('downloadAllBtn').onclick=async ()=>{
   for(let i=0;i<allLoras.length;i++){
       downloadLora(encodeURIComponent(allLoras[i].name));
       await new Promise(r=>setTimeout(r,500));
   }
}

window.onload=loadLoraList;
</script>
</body>
</html>
"""
    return web.Response(text=html_content, content_type="text/html")


# ---------------------------------------
# Download existing LoRA -> send to user
# ---------------------------------------
@PromptServer.instance.routes.get("/lora_downloader/download_file/{filename:.+}")
async def download_lora_file(request):
    try:
        filename = urllib.parse.unquote(request.match_info["filename"])
        lora_directory = folder_paths.get_folder_paths("loras")[0]

        try:
            file_path = safe_join(lora_directory, filename)
        except ValueError:
            return web.json_response({"error": "Forbidden"}, status=403)

        if not os.path.exists(file_path):
            return web.json_response({"error": "File not found"}, status=404)

        return web.FileResponse(
            file_path,
            headers={
                "Content-Disposition": f'attachment; filename="{os.path.basename(file_path)}"'
            },
        )

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ---------------------------------------
# Node mappings
# ---------------------------------------
NODE_CLASS_MAPPINGS = {
    "LoraDownloader": LoraDownloader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraDownloader": "LoRA Downloader"
}
