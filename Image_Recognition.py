import requests
import json
import pandas as pd
from pathlib import Path

# Ollama API 的基础URL (默认是本地)
OLLAMA_API_BASE = "http://localhost:11434"

import base64


def analyze_image_with_ollama_api(image_path, model='llava'):
    """
    使用Ollama的HTTP API分析单张图片，并确保图片数据被编码为base64。

    Args:
        image_path (str): 图片文件的路径。
        model (str): 要使用的Ollama模型名称。

    Returns:
        str: 模型生成的图片描述，如果失败则返回错误信息。
    """
    # API 端点
    api_url = "http://localhost:11434/api/generate"

    try:
        # 读取图片文件为二进制数据
        with open(image_path, 'rb') as file:
            image_data = file.read()

        # 将二进制数据编码为base64字符串
        encoded_image_data = base64.b64encode(image_data).decode('utf-8')

        # 准备要发送的JSON数据
        payload = {
            "model": model,
            "prompt": "请详细描述这张图片的内容。",
            "images": [encoded_image_data],  # 使用base64编码的图片数据
            "stream": False #/ 设置为False以获得完整响应
        }

        # 发送POST请求
        response = requests.post(api_url, json=payload)

        # 检查HTTP状态码
        if response.status_code != 200:
            return f"HTTP Error {response.status_code}: {response.text}"

        # 解析JSON响应
        result = response.json()
        return result.get('response', 'No response field in result').strip()

    except Exception as e:
        return f"❌ 处理 {image_path} 时发生未知错误: {str(e)}"


def main():
    # === 配置区域 ===
    images_folder = r"C:\Users\16846\Desktop\保密\PDF2WEB\extracted\test\images"  # <-- 修改为你的图片文件夹路径
    output_excel = "image_descriptions_api.xlsx"
    model_name = "qwen2.5vl:7b"  # 确保这个模型已经通过 `ollama run llava` 下载
    # === 配置结束 ===

    folder_path = Path(images_folder)
    if not folder_path.exists():
        print(f"❌ 错误：指定的图片文件夹不存在: {images_folder}")
        return

    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
    image_files = [f for f in folder_path.iterdir()
                   if f.is_file() and f.suffix.lower() in image_extensions]

    if not image_files:
        print(f"❌ 在文件夹 {images_folder} 中未找到任何支持的图片文件。")
        return

    print(f"✅ 找到 {len(image_files)} 张图片，开始通过API分析...")

    results = []

    for idx, image_file in enumerate(image_files, 1):
        print(f"  ({idx}/{len(image_files)}) 正在处理: {image_file.name}")
        description = analyze_image_with_ollama_api(str(image_file), model=model_name)
        results.append({
            'Image Path': str(image_file.resolve()),
            'Image Name': image_file.name,
            'Description': description
        })

    # 创建DataFrame并保存到Excel
    df = pd.DataFrame(results)
    try:
        df.to_excel(output_excel, index=False)
        print(f"\n🎉 成功！结果已保存到 '{output_excel}'")
        print(f"共处理了 {len(results)} 张图片。")
    except Exception as e:
        print(f"❌ 保存Excel文件失败: {e}")


if __name__ == "__main__":
    main()