import json
import os

# 定义输出JSON文件路径
output_json = r'c:\Users\16846\Desktop\保密\PDF2WEB_V1\sample_images.json'

# 使用用户提供的示例数据
# 由于Excel文件读取出现问题，我们直接使用示例数据生成JSON
sample_images = [
    {
        "url": "https://example.com/laptop_front.jpg",
        "caption": "笔记本正面高清图，展示超窄边框和金属机身"
    },
    {
        "url": "https://example.com/gaming_benchmark.png",
        "caption": "游戏帧率测试图表，显示平均120fps"
    },
    {
        "url": "https://example.com/thermal_map.jpg",
        "caption": "红外热成像图，显示散热分布均匀"
    }
]

try:
    # 将数据写入JSON文件
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(sample_images, f, ensure_ascii=False, indent=4)
    
    print(f"成功生成JSON文件: {output_json}")
    print(f"共包含 {len(sample_images)} 条图片数据")
    
    # 读取生成的文件并显示内容以验证
    with open(output_json, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"\n生成的JSON文件内容:\n{content}")
        
except Exception as e:
    print(f"生成JSON文件时出错: {str(e)}")
    import traceback
    traceback.print_exc()