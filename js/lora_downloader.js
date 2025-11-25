import { app } from "/scripts/app.js";

// 添加一个菜单项来打开LoRA下载器
app.registerExtension({
    name: "LoraDownloader.Extension",
    async setup() {
        // 创建一个新的菜单项
        const menu = document.querySelector(".comfy-menu");
        if (menu) {
            const separator = document.createElement("hr");
            separator.style.margin = "10px 0";
            menu.appendChild(separator);
            
            const button = document.createElement("button");
            button.textContent = "LoRA 下载器";
            button.onclick = () => {
                // 打开新的窗口或标签页显示LoRA下载器
                window.open("/lora_downloader", "_blank");
            };
            menu.appendChild(button);
        }
    }
});

// 添加HTTP路由来服务前端页面
const { api } = require("/scripts/api.js");

// 注册静态文件路由
async function registerStaticRoutes() {
    try {
        // 这里我们假设ComfyUI会自动服务web目录下的文件
        console.log("LoRA Downloader extension loaded");
    } catch (error) {
        console.error("Failed to register static routes:", error);
    }
}

registerStaticRoutes();
