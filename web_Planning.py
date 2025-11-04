# ai_ppt_agent.py
# 基于文本和图片自动生成PPT代码提示词的智能体（修复 chat_history 错误）

from langchain_ollama import ChatOllama
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import json

# ==================== 配置 ====================
os.environ["LANGCHAIN_TRACING_V2"] = "false"  # 可选

# 初始化本地大模型
llm = ChatOllama(
    model="qwen2.5:7b",           # 确保这个模型已加载
    temperature=0.3,
    base_url="http://localhost:11434",
    num_predict=4096
)

# ==================== 工具定义 ====================

# --- 工具1：提取重点 ---
key_points_prompt = PromptTemplate.from_template(
    "请从以下文本中提取3-5个最重要的要点。\n\n文本：{text}"
)
key_points_chain = LLMChain(llm=llm, prompt=key_points_prompt)

def extract_key_points(text: str) -> str:
    result = key_points_chain.invoke({"text": text})
    return result["text"].strip()

# --- 工具2：生成提纲 ---
outline_prompt = PromptTemplate.from_template(
    "请根据以下文本生成一个逻辑清晰的提纲，包含3-5个主要章节。\n\n文本：{text}"
)
outline_chain = LLMChain(llm=llm, prompt=outline_prompt)

def generate_outline(text: str) -> str:
    result = outline_chain.invoke({"text": text})
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
image_usage_chain = LLMChain(llm=llm, prompt=image_usage_prompt)

def analyze_image_usage(image_info: str) -> str:
    try:
        info = json.loads(image_info)
        result = image_usage_chain.invoke({
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
final_prompt_chain = LLMChain(llm=llm, prompt=final_prompt_template)

def generate_final_ppt_prompt(inputs: str) -> str:
    try:
        data = json.loads(inputs)
        result = final_prompt_chain.invoke({
            "text": data["text"],
            "outline": data["outline"],
            "image_suggestions": data["image_suggestions"]
        })
        return result["text"].strip()
    except Exception as e:
        return f"生成最终提示词失败：{str(e)}"

# ==================== 工具列表 ====================
tools = [
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

# ==================== 修复关键：使用 ZERO_SHOT 而不是 CONVERSATIONAL ====================
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # ✅ 修复：不需要 chat_history
    verbose=True,
    handle_parsing_errors=True
)

# ==================== 主接口函数 ====================
def create_ppt_code_prompt(
    text: str,
    images: list  # [{"url": "...", "caption": "..."}, ...]
):
    print("🔍 正在分析文本内容...")
    outline = agent.invoke({"input": f"请为以下文本生成提纲：\n{text}"})["output"]

    print("🖼️ 正在分析图片使用建议...")
    image_suggestions = []
    for i, img in enumerate(images):
        print(f"  → 分析图片 {i+1}: {img['url']}")
        img_json = json.dumps(img, ensure_ascii=False)
        suggestion = agent.invoke({
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

    final_prompt = agent.invoke({
        "input": f"请整合以下信息，生成PPT代码提示词：{final_input_json}"
    })["output"]

    return {
        "success": True,
        "message": "PPT提示词生成成功",
        "result": {
            "summary": agent.invoke({"input": f"请用一句话总结文本：\n{text}"})["output"],
            "key_points": agent.invoke({"input": f"请提取重点：\n{text}"})["output"],
            "outline": outline,
            "image_suggestions": image_suggestions,
            "final_ppt_prompt": final_prompt  # ← 可喂给 Code Llama 等生成代码
        }
    }

# ==================== 示例运行 ====================
if __name__ == "__main__":
    # 示例文本
    sample_text = """
    这款笔记本电脑性能很强，打游戏非常流畅，散热也不错。
    但是重量有点重，携带不方便，适合固定场所使用。
    总体来说性价比还可以。

    笔记本电脑采用了最新的处理器，内存容量大，存储空间充裕。
    屏幕分辨率高，显示效果细腻。
    散热系统经过优化，长时间使用也不会过热。
    """

    # 示例图片
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

    print("=" * 60)
    print("🚀 AI 自动PPT生成智能体（图文版）")
    print("=" * 60)
    print("模型：qwen2.5:7b (Ollama)")
    print("功能：从文本+图片生成PPT代码提示词")
    print("-" * 60)

    try:
        result = create_ppt_code_prompt(sample_text, sample_images)

        if result["success"]:
            print("\n✅ 成功生成最终提示词！")
            print("\n" + "="*60)
            print("📄 可用于生成PPT代码的提示词：")
            print("="*60)
            print(result["result"]["final_ppt_prompt"])
        else:
            print(f"❌ 错误：{result['message']}")

    except Exception as e:
        print(f"❌ 执行失败：{str(e)}")
        print("请确保已运行：ollama run qwen2.5:7b")