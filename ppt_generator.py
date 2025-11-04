# ppt_generator.py
# 基于本地大模型的PPT生成器
# 参考：https://github.com/Zaneph1/AI-agent-PPT-Generator

import os
import json
import pandas as pd
from langchain_ollama import ChatOllama
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

class PPTGenerator:
    """
    AI PPT 生成器
    基于本地Ollama大模型，支持从文本和图片生成PPT代码提示词
    """
    
    def __init__(self, model="qwen2.5:7b", temperature=0.3, base_url="http://localhost:11434"):
        """
        初始化PPT生成器
        
        参数:
            model: 使用的LLM模型名称
            temperature: 生成温度参数
            base_url: Ollama服务地址
        """
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
        
        # 初始化本地大模型
        self.llm = ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
            num_predict=4096
        )
        
        # 初始化工具和智能体
        self._init_tools()
        self._init_agent()
        
        print(f"✅ PPTGenerator已初始化，使用模型: {model}")
    
    def _init_tools(self):
        """
        初始化所有工具函数
        """
        # --- 工具1：提取重点 ---
        key_points_prompt = PromptTemplate.from_template(
            "请从以下文本中提取3-5个最重要的要点。\n\n文本：{text}"
        )
        self.key_points_chain = LLMChain(llm=self.llm, prompt=key_points_prompt)
        
        def extract_key_points(text: str) -> str:
            result = self.key_points_chain.invoke({"text": text})
            return result["text"].strip()
        
        # --- 工具2：生成提纲 ---
        outline_prompt = PromptTemplate.from_template(
            "请根据以下文本生成一个逻辑清晰的提纲，包含3-5个主要章节。\n\n文本：{text}"
        )
        self.outline_chain = LLMChain(llm=self.llm, prompt=outline_prompt)
        
        def generate_outline(text: str) -> str:
            result = self.outline_chain.invoke({"text": text})
            return result["text"].strip()
        
        # --- 工具3：分析图片用途 ---
        image_usage_prompt = PromptTemplate.from_template(
            """
            你是一个PPT视觉设计专家。请根据图片描述判断其最适合插入PPT的哪个部分。

            图片URL: {image_url}
            描述: {caption}

            请回答：
            - 建议插入章节：
            - 用途（如产品展示、数据对比等）：
            - 布局建议（如居中大图、侧边配文等）：
            """
        )
        self.image_usage_chain = LLMChain(llm=self.llm, prompt=image_usage_prompt)
        
        def analyze_image_usage(image_info: str) -> str:
            try:
                info = json.loads(image_info)
                result = self.image_usage_chain.invoke({
                    "image_url": info["url"],
                    "caption": info["caption"]
                })
                return result["text"].strip()
            except Exception as e:
                return f"图片解析失败：{str(e)}"
        
        # --- 工具4：生成最终PPT代码提示词 ---
        final_prompt_template = PromptTemplate.from_template(
            """
            请根据以下信息，生成一段**详细、结构清晰的提示词**，用于指导大模型生成PPT代码（如 Reveal.js / HTML / python-pptx）。

            =============== 输入信息 ===============
            【核心文本】
            {text}

            【结构提纲】
            {outline}

            【图片使用建议】
            {image_suggestions}

            =============== 输出要求 ===============
            请生成提示词，包含：
            1. PPT整体风格（如科技感、极简风、商务蓝等）
            2. 每页标题、内容要点、布局（图文排版注意并列，递进关系）
            3. 图片插入位置（直接使用URL）
            4. 是否需要动画、图表、过渡效果
            5. 推荐输出格式（如 HTML+CSS+JS 或 Python脚本）
            6. 需要有目录页
            请确保提示词足够详细，能让代码生成模型准确生成PPT代码。
            """
        )
        self.final_prompt_chain = LLMChain(llm=self.llm, prompt=final_prompt_template)
        
        def generate_final_ppt_prompt(inputs: str) -> str:
            try:
                data = json.loads(inputs)
                result = self.final_prompt_chain.invoke({
                    "text": data["text"],
                    "outline": data["outline"],
                    "image_suggestions": data["image_suggestions"]
                })
                return result["text"].strip()
            except Exception as e:
                return f"生成最终提示词失败：{str(e)}"
        
        # 工具列表
        self.tools = [
            Tool(
                name="Extract Key Points",
                func=extract_key_points,
                description="从文本中提取最重要的要点"
            ),
            Tool(
                name="Generate Outline",
                func=generate_outline,
                description="生成逻辑清晰的提纲"
            ),
            Tool(
                name="Analyze Image Usage",
                func=analyze_image_usage,
                description="分析每张图片的用途与布局建议"
            ),
            Tool(
                name="Generate Final PPT Prompt",
                func=generate_final_ppt_prompt,
                description="整合图文信息，生成用于生成PPT代码的最终提示词"
            )
        ]
    
    def _init_agent(self):
        """
        初始化智能体
        """
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,  # 设置为True可查看详细过程
            handle_parsing_errors=True
        )
    
    def load_images_from_folder(self, folder_path, max_images=10):
        """
        从文件夹加载图片信息
        
        参数:
            folder_path: 图片文件夹路径
            max_images: 最大加载图片数量
        
        返回:
            图片信息列表 [{"url": "...", "caption": "..."}]
        """
        if not os.path.exists(folder_path):
            print(f"❌ 图片文件夹不存在: {folder_path}")
            return []
        
        # 检查是否有Excel描述文件
        excel_path = os.path.join(os.path.dirname(folder_path), "image_descriptions_api.xlsx")
        image_descriptions = {}
        
        if os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path)
                if 'Image Path' in df.columns and 'Description' in df.columns:
                    for _, row in df.iterrows():
                        image_name = os.path.basename(row['Image Path'])
                        image_descriptions[image_name] = row['Description']
            except Exception as e:
                print(f"⚠️  读取图片描述Excel失败: {str(e)}")
        
        # 加载图片文件
        image_files = [f for f in os.listdir(folder_path) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        image_files = image_files[:max_images]
        
        images = []
        for img_file in image_files:
            # 创建本地文件URL
            img_path = os.path.join(folder_path, img_file)
            img_url = f"file:///{img_path.replace('\\', '/')}"
            
            # 获取描述，如果有
            caption = image_descriptions.get(img_file, f"图片: {img_file}")
            
            images.append({
                "url": img_url,
                "caption": caption
            })
        
        print(f"📷 已加载 {len(images)} 张图片")
        return images
    
    def generate(self, text, title=None, style="professional", images=None, image_folder=None, use_cloud_enhance=False):
        """
        生成PPT代码提示词
        
        参数:
            text: 输入文本内容
            title: PPT标题（可选）
            style: PPT风格（professional, creative, minimal等）
            images: 图片列表 [{"url": "...", "caption": "..."}]（可选）
            image_folder: 图片文件夹路径（可选）
            use_cloud_enhance: 是否使用云端增强（暂未实现）
        
        返回:
            生成的PPT代码提示词
        """
        print("🚀 开始生成PPT提示词...")
        
        # 如果提供了图片文件夹，从文件夹加载图片
        if image_folder:
            images = self.load_images_from_folder(image_folder)
        elif images is None:
            images = []
        
        # 如果指定了标题，添加到文本开头
        if title:
            full_text = f"标题: {title}\n\n{text}"
        else:
            full_text = text
        
        # 根据风格调整提示词
        if style != "professional":
            # 在最终提示词中加入风格要求
            original_template = self.final_prompt_chain.prompt.template
            style_instruction = f"\n7. 风格要求：请使用{style}风格设计PPT，包括配色、字体和布局"
            self.final_prompt_chain.prompt.template = original_template + style_instruction
        
        # 调用核心功能生成PPT提示词
        result = self._create_ppt_prompt(full_text, images)
        
        # 还原原始模板
        if style != "professional":
            self._init_tools()  # 重新初始化以恢复原始模板
        
        # 保存结果到文件
        output_file = "generated_ppt_prompt.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["result"]["final_ppt_prompt"])
        
        print(f"✅ PPT提示词生成完成！已保存到: {output_file}")
        print(f"📄 提示词长度: {len(result['result']['final_ppt_prompt'])} 字符")
        
        return output_file
    
    def _create_ppt_prompt(self, text, images):
        """
        创建PPT提示词的核心方法
        """
        print("🔍 正在分析文本内容...")
        outline = self.agent.invoke({"input": f"请为以下文本生成提纲：\n{text}"})["output"]

        image_suggestions = []
        if images:
            print(f"🖼️ 正在分析 {len(images)} 张图片的使用建议...")
            for i, img in enumerate(images):
                print(f"  → 分析图片 {i+1}: {os.path.basename(img['url'])}")
                img_json = json.dumps(img, ensure_ascii=False)
                suggestion = self.agent.invoke({
                    "input": f"请分析这张图片的用途：{img_json}"
                })["output"]
                image_suggestions.append(f"【图片{i+1}】\n{suggestion}")
        
        image_suggestions_str = "\n\n".join(image_suggestions)

        print("🎯 正在生成最终PPT代码提示词...")
        final_inputs = {
            "text": text,
            "outline": outline,
            "image_suggestions": image_suggestions_str
        }
        final_input_json = json.dumps(final_inputs, ensure_ascii=False)

        final_prompt = self.agent.invoke({
            "input": f"请整合以下信息，生成PPT代码提示词：{final_input_json}"
        })["output"]

        return {
            "success": True,
            "message": "PPT提示词生成成功",
            "result": {
                "summary": self.agent.invoke({"input": f"请用一句话总结文本：\n{text}"})["output"],
                "key_points": self.agent.invoke({"input": f"请提取重点：\n{text}"})["output"],
                "outline": outline,
                "image_suggestions": image_suggestions,
                "final_ppt_prompt": final_prompt
            }
        }
    
    def batch_generate(self, texts, titles=None, style="professional"):
        """
        批量生成多个PPT提示词
        
        参数:
            texts: 文本列表
            titles: 标题列表（可选）
            style: PPT风格
        
        返回:
            生成的文件路径列表
        """
        results = []
        
        for i, text in enumerate(texts):
            title = titles[i] if titles and i < len(titles) else f"演示文稿 {i+1}"
            print(f"\n=== 正在生成第 {i+1}/{len(texts)} 个PPT ===")
            file_path = self.generate(text, title, style)
            results.append(file_path)
        
        return results

# 示例使用
if __name__ == "__main__":
    # 初始化生成器
    generator = PPTGenerator()
    
    # 准备输入文本
    input_text = """
    这款笔记本电脑性能很强，打游戏非常流畅，散热也不错。
    但是重量有点重，携带不方便，适合固定场所使用。
    总体来说性价比还可以。

    笔记本电脑采用了最新的处理器，内存容量大，存储空间充裕。
    屏幕分辨率高，显示效果细腻。
    散热系统经过优化，长时间使用也不会过热。
    """
    
    # 使用本地图片文件夹
    img_folder = "img"  # 相对路径，假设当前工作目录下有img文件夹
    
    # 生成PPT提示词
    ppt_path = generator.generate(
        text=input_text,
        title="笔记本电脑性能分析",
        style="professional",
        image_folder=img_folder,
        use_cloud_enhance=False
    )
    
    print(f"\n🎉 PPT提示词已成功生成: {ppt_path}")
    print("\n📋 使用提示：")
    print("1. 打开生成的txt文件复制提示词")
    print("2. 将提示词粘贴到代码生成模型中")
    print("3. 获取完整的PPT代码并保存为HTML或其他格式")