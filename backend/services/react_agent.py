"""
ReAct Agent 实现
真正的 Reasoning + Acting 循环架构

模型分工：
- Agent 推理/规划: qwen3-coder-plus
- 文章写作: deepseek-v3  
- 图像识别: qwen3-vl-plus
"""

import json
import re
import openai
from typing import Dict, Any, List, Optional, Callable

# 模型配置
# 模型配置（硬编码）
MODELS = {
    "agent": "qwen3-coder-plus",      # Agent 推理/规划
    "writer": "deepseek-v3",           # 文章写作
    "vision": "qwen3-vl-plus",         # 图像识别
}

# API 地址（硬编码）
IFLOW_API_BASE = "https://apis.iflow.cn/v1"

# ReAct Prompt 模板（从环境变量读取）
import os

DEFAULT_REACT_PROMPT = """你是微信公众号创作助手，使用 ReAct 框架完成任务。

## 可用工具

1. **write_article** - 创作/改写文章
   参数: {"instruction": "写作要求"}

2. **apply_theme** - 应用排版（需要先有文章）
   参数: {"theme": "主题名"}
   可选: professional, magazine, minimalist_notion, elegant, fresh, xiaohongshu

3. **generate_cover** - 生成封面图（需要先有文章）
   参数: {"style": "风格描述"}

## 格式（严格遵守）

调用工具时:
Thought: [简短思考]
Action: [工具名]
Action Input: {"参数": "值"}

直接回复时:
Thought: [简短思考]
Final Answer: [回复内容]

## 关键规则

1. **没有文章时，只能用 write_article 或 Final Answer**
2. apply_theme 和 generate_cover 必须在有文章后才能调用
3. 不要自己编造文章内容，必须通过 write_article 工具
4. 简单问候直接用 Final Answer
5. 一次只调用一个工具

## 当前状态
%s
"""

DEFAULT_REACT_EXAMPLES = """
## 示例（严格按此格式输出）

用户: 写一篇时间管理的文章
Thought: 用户要写文章，调用 write_article
Action: write_article
Action Input: {"instruction": "写一篇时间管理的干货文章，1500字"}

用户: 排版一下 / 换个排版 / 换个风格（当前有文章）
Thought: 有文章，执行排版
Action: apply_theme
Action Input: {"theme": "magazine"}

用户: 用小红书风格排版（当前有文章）
Thought: 用户指定小红书风格
Action: apply_theme
Action Input: {"theme": "xiaohongshu"}

用户: 生成封面（当前有文章和标题）
Thought: 有标题，生成封面
Action: generate_cover
Action Input: {"style": "专业简约"}

用户: 排版 / 封面（当前无文章）
Thought: 还没有文章
Final Answer: 还没有文章内容，先告诉我你想写什么？

用户: 你好
Thought: 问候
Final Answer: 你好！告诉我你想写什么文章吧。

【重要】当用户说"换个排版/风格"时，必须直接调用 apply_theme，不要解释"可以调用"！
"""

def get_react_prompt():
    return os.environ.get("PROMPT_REACT_AGENT", DEFAULT_REACT_PROMPT)

def get_react_examples():
    return os.environ.get("PROMPT_REACT_EXAMPLES", DEFAULT_REACT_EXAMPLES)


class ReActAgent:
    """ReAct Agent 实现"""
    
    def __init__(self, api_key: str, api_base: str = "https://apis.iflow.cn/v1"):
        self.api_key = api_key
        self.api_base = api_base
        self.client = openai.OpenAI(api_key=api_key, base_url=api_base)
        self.tools: Dict[str, Callable] = {}
        self.max_iterations = 5  # 最大循环次数
        
    def register_tool(self, name: str, func: Callable, description: str = ""):
        """注册工具"""
        self.tools[name] = {
            "func": func,
            "description": description
        }
        
    def _build_messages(self, user_input: str, context: Dict, history: List[Dict]) -> List[Dict]:
        """构建消息列表"""
        context_str = f"""
- 当前文章: {'有' if context.get('hasArticle') else '无'}
- 文章字数: {context.get('articleLength', 0)}
- 标题: {context.get('title', '未设置')}
- 当前排版: {context.get('theme', 'professional')}
- 封面: {'已生成' if context.get('hasCover') else '未生成'}
"""
        
        system_prompt = (get_react_prompt() % context_str) + get_react_examples()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史对话（最近几轮）
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})
            
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _parse_response(self, response: str) -> Dict:
        """解析 Agent 响应"""
        result = {
            "thought": "",
            "action": None,
            "action_input": None,
            "final_answer": None
        }
        
        # 提取 Thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|Final Answer:|$)', response, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
            
        # 提取 Final Answer
        final_match = re.search(r'Final Answer:\s*(.+?)$', response, re.DOTALL)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result
            
        # 提取 Action
        action_match = re.search(r'Action:\s*(\w+)', response)
        if action_match:
            result["action"] = action_match.group(1).strip()
            
        # 提取 Action Input
        input_match = re.search(r'Action Input:\s*(\{.+?\})', response, re.DOTALL)
        if input_match:
            try:
                result["action_input"] = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                result["action_input"] = {"raw": input_match.group(1)}
                
        return result
    
    def run(self, user_input: str, context: Dict = None, history: List[Dict] = None) -> Dict:
        """
        执行 ReAct 循环
        
        Returns:
            {
                "success": bool,
                "thought": str,          # Agent 的思考过程
                "action": str,           # 调用的工具
                "action_input": dict,    # 工具参数
                "observation": str,      # 工具返回结果
                "final_answer": str,     # 最终回复
                "iterations": int        # 循环次数
            }
        """
        context = context or {}
        history = history or []
        
        messages = self._build_messages(user_input, context, history)
        iterations = 0
        
        while iterations < self.max_iterations:
            iterations += 1
            
            # 调用 Agent 模型
            print(f"🤖 [ReAct] 第 {iterations} 轮推理，使用模型: {MODELS['agent']}")
            
            try:
                response = self.client.chat.completions.create(
                    model=MODELS["agent"],
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7
                )
                agent_output = response.choices[0].message.content
                print(f"🤖 [ReAct] Agent 输出:\n{agent_output[:500]}...")
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Agent 调用失败: {str(e)}",
                    "iterations": iterations
                }
            
            # 解析响应
            parsed = self._parse_response(agent_output)
            
            # 如果有 Final Answer，任务完成
            if parsed["final_answer"]:
                return {
                    "success": True,
                    "thought": parsed["thought"],
                    "final_answer": parsed["final_answer"],
                    "iterations": iterations
                }
            
            # 如果有 Action，返回给前端执行
            if parsed["action"]:
                tool_name = parsed["action"]
                tool_input = parsed["action_input"] or {}
                
                print(f"🔧 [ReAct] 需要执行工具: {tool_name}, 参数: {tool_input}")
                
                # 返回工具调用信息给前端
                return {
                    "success": True,
                    "thought": parsed["thought"],
                    "action": tool_name,
                    "action_input": tool_input,
                    "iterations": iterations,
                    "needs_tool_execution": True
                }
            
            # 如果没有有效的 Action 也没有 Final Answer
            # 可能是格式问题，尝试让 Agent 重新思考
            messages.append({"role": "assistant", "content": agent_output})
            messages.append({"role": "user", "content": "请按照 ReAct 格式回复，使用 Thought/Action/Action Input 或 Final Answer。"})
        
        # 超过最大循环次数
        return {
            "success": False,
            "error": "Agent 推理超过最大循环次数",
            "iterations": iterations
        }


def create_agent(api_key: str, api_base: str = "https://apis.iflow.cn/v1") -> ReActAgent:
    """创建并配置 Agent"""
    agent = ReActAgent(api_key, api_base)
    
    # 工具会在调用时动态注入，因为需要访问 Flask 上下文
    # 这里只是创建 Agent 实例
    
    return agent

