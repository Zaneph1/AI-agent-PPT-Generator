import pandas as pd
import json
import os

# 定义Excel文件路径
excel_file = r'c:\Users\16846\Desktop\保密\PDF2WEB_V1\image_descriptions_api.xlsx'
# 定义输出JSON文件路径
output_json = r'c:\Users\16846\Desktop\保密\PDF2WEB_V1\sample_images.json'

try:
    # 检查文件是否存在
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Excel文件不存在: {excel_file}")
    
    print(f"开始读取Excel文件: {excel_file}")
    
    # 尝试不同的方法读取Excel文件
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
    except:
        df = pd.read_excel(excel_file)
    
    print(f"成功读取Excel文件，共 {len(df)} 行数据")
    print(f"Excel文件中的列: {list(df.columns)}")
    
    # 尝试查找可能的列名变体
    columns = [col.strip() for col in df.columns]
    print(f"清理后的列名: {columns}")
    
    # 定义可能的列名变体
    path_column = None
    desc_column = None
    
    # 查找Image Path相关的列
    for col in columns:
        if 'path' in col.lower() or 'url' in col.lower() or '图片' in col:
            path_column = df.columns[columns.index(col)]
            break
    
    # 查找Description相关的列
    for col in columns:
        if 'desc' in col.lower() or '描述' in col or '说明' in col:
            desc_column = df.columns[columns.index(col)]
            break
    
    # 如果找不到合适的列，尝试使用前两列
    if not path_column and not desc_column and len(columns) >= 2:
        print("警告: 无法识别标准列名，尝试使用前两列")
        path_column = df.columns[0]
        desc_column = df.columns[1]
    
    print(f"使用的路径列: {path_column}")
    print(f"使用的描述列: {desc_column}")
    
    # 创建sample_images列表
    sample_images = []
    
    # 遍历Excel数据，构建字典列表
    for index, row in df.iterrows():
        try:
            path_value = row[path_column]
            desc_value = row[desc_column]
            
            # 检查行数据是否为空
            if pd.notna(path_value) and pd.notna(desc_value):
                image_entry = {
                    "url": str(path_value).strip(),
                    "caption": str(desc_value).strip()
                }
                sample_images.append(image_entry)
                # 打印前几行数据作为示例
                if index < 3:
                    print(f"示例数据 {index+1}: {image_entry}")
        except Exception as e:
            print(f"处理行 {index+1} 时出错: {str(e)}")
    
    # 生成JSON格式的内容 - 注意这里直接生成sample_images列表
    # 而不是包装在字典中，以符合用户要求的格式
    
    # 将数据写入JSON文件
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(sample_images, f, ensure_ascii=False, indent=4)
    
    print(f"成功生成JSON文件: {output_json}")
    print(f"共处理了 {len(sample_images)} 条图片数据")
    
    # 读取生成的文件并显示前100个字符以验证格式
    with open(output_json, 'r', encoding='utf-8') as f:
        preview = f.read(100)
        print(f"生成的JSON文件预览: {preview}...")
    
except FileNotFoundError as e:
    print(f"错误: {str(e)}")
except Exception as e:
    print(f"处理过程中发生错误: {str(e)}")
    import traceback
    traceback.print_exc()