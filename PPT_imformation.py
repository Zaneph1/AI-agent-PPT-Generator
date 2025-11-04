# ppt_text_agent.py

from langchain_ollama import ChatOllama
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

# 设置环境变量（可选）
os.environ["LANGCHAIN_TRACING_V2"] = "false"  # 关闭追踪，除非你用了 LangSmith

# === 初始化本地大模型（通过 Ollama）===
# 可替换 model 为你本地加载的模型名，如 llama3, qwen:7b, phi3 等
llm = ChatOllama(
    model="qwen2.5:7b",  # 改成你想用的本地模型
    temperature=0.3,
    base_url="http://localhost:11434",  # 默认地址
    num_predict=512  # 可选：限制生成长度
)

# === 工具1：提取重点 ===
key_points_prompt = PromptTemplate.from_template(
    "请从以下文本中提取出3-5个最重要的要点。\n\n文本：{text}"
)
key_points_chain = LLMChain(llm=llm, prompt=key_points_prompt)


def extract_key_points(text: str) -> str:
    result = key_points_chain.invoke({"text": text})
    return result["text"].strip()


# === 工具2：生成提纲 ===
outline_prompt = PromptTemplate.from_template(
    "请根据以下文本生成一个逻辑清晰的提纲，包含3-5个主要章节。\n\n文本：{text}"
)
outline_chain = LLMChain(llm=llm, prompt=outline_prompt)


def generate_outline(text: str) -> str:
    result = outline_chain.invoke({"text": text})
    return result["text"].strip()


# === 工具3：PPT 制作思路 ===
ppt_suggestions_prompt = PromptTemplate.from_template(
    "请为以下文本设计一个适合制作 PPT 的思路，包括标题、副标题和每个章节的小节标题。\n\n文本：{text}"
)
ppt_suggestions_chain = LLMChain(llm=llm, prompt=ppt_suggestions_prompt)


def suggest_ppt_structure(text: str) -> str:
    result = ppt_suggestions_chain.invoke({"text": text})
    return result["text"].strip()


# === 定义工具列表 ===
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
        name="Suggest PPT Structure",
        func=suggest_ppt_structure,
        description="设计适合制作 PPT 的思路"
    )
]

# === 初始化智能体 ===
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,  # 显示 agent 的思考过程
    handle_parsing_errors=True
)


# === 主函数：运行智能体分析 ===
def analyze_text_for_ppt(input_text: str):
    prompt = f"""
    请对以下文本进行全面理解与分析，目的是为其创建一个清晰的 PPT 结构：

    {input_text}

    请依次完成：
    1. 提取重点
    2. 生成提纲
    3. 设计 PPT 制作思路

    请以清晰的格式输出结果。
    """
    result = agent.invoke({"input": prompt})
    return result["output"]


# === 示例调用 ===
if __name__ == "__main__":
    sample_text = """
    这款笔记本电脑性能很强，打游戏非常流畅，散热也不错。
    但是重量有点重，携带不方便，适合固定场所使用。
    总体来说性价比还可以。

    笔记本电脑采用了最新的处理器，内存容量大，存储空间充裕。
    屏幕分辨率高，显示效果细腻。
    散热系统经过优化，长时间使用也不会过热。
    """

    print("🔍 正在使用本地 Ollama 模型分析文本...\n")
    result = analyze_text_for_ppt(sample_text)
    print("\n✅ 分析结果：")
    print(result)