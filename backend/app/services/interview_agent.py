"""
面试Agent核心 - LangGraph工作流实现
用户是面试官，Agent是面试者
"""
import json
import uuid
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.services.llm_factory import llm_factory
from app.models.database import LLMConfig


class InterviewState(TypedDict):
    """面试状态定义"""
    messages: Annotated[List[BaseMessage], operator.add]  # 对话历史
    session_id: str  # 会话ID
    user_id: str  # 用户ID
    current_phase: str  # 当前面试阶段
    resume_data: Dict  # 简历数据
    job_info: Dict  # 岗位信息
    knowledge_context: List[str]  # 知识库上下文
    thinking_process: List[Dict]  # 思考过程（用于可视化）
    llm_config: Optional[LLMConfig]  # LLM配置


class InterviewAgent:
    """面试Agent - 扮演面试者角色"""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建LangGraph工作流"""
        
        # 定义状态图
        workflow = StateGraph(InterviewState)
        
        # 添加节点
        workflow.add_node("understand_question", self._understand_question)
        workflow.add_node("retrieve_knowledge", self._retrieve_knowledge)
        workflow.add_node("organize_answer", self._organize_answer)
        workflow.add_node("generate_response", self._generate_response)
        
        # 定义边
        workflow.set_entry_point("understand_question")
        workflow.add_edge("understand_question", "retrieve_knowledge")
        workflow.add_edge("retrieve_knowledge", "organize_answer")
        workflow.add_edge("organize_answer", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _understand_question(self, state: InterviewState) -> Dict:
        """理解面试官问题"""
        
        # 获取最后一条用户消息（面试官的问题）
        last_message = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_message = msg.content
                break
        
        if not last_message:
            return {"thinking_process": [{"step": "理解问题", "status": "error", "detail": "未找到面试官问题"}]}
        
        # 分析问题类型
        question_type = self._analyze_question_type(last_message)
        
        thinking = {
            "step": "理解问题",
            "status": "completed",
            "detail": f"面试官问题: {last_message[:100]}...",
            "question_type": question_type
        }
        
        return {
            "current_phase": question_type,
            "thinking_process": [thinking]
        }
    
    def _analyze_question_type(self, question: str) -> str:
        """分析问题类型"""
        question_lower = question.lower()
        
        if any(kw in question_lower for kw in ["介绍", "自我", "你好", "是谁"]):
            return "self_intro"
        elif any(kw in question_lower for kw in ["项目", "做过", "负责", "参与"]):
            return "project_experience"
        elif any(kw in question_lower for kw in ["技术", "原理", "实现", "设计", "架构"]):
            return "technical"
        elif any(kw in question_lower for kw in ["团队", "冲突", "沟通", "协作", "压力"]):
            return "behavioral"
        elif any(kw in question_lower for kw in ["薪资", "期望", "待遇", "工资"]):
            return "salary"
        elif any(kw in question_lower for kw in ["问题", "想问", "了解"]):
            return "qa"
        else:
            return "general"
    
    def _retrieve_knowledge(self, state: InterviewState) -> Dict:
        """从知识库检索相关信息"""
        
        # 这里简化处理，实际应该调用向量检索
        # 从state中获取知识库上下文
        knowledge_context = state.get("knowledge_context", [])
        
        thinking = {
            "step": "知识检索",
            "status": "completed",
            "detail": f"检索到 {len(knowledge_context)} 条相关知识"
        }
        
        return {
            "thinking_process": state.get("thinking_process", []) + [thinking]
        }
    
    def _organize_answer(self, state: InterviewState) -> Dict:
        """组织回答结构"""
        
        phase = state.get("current_phase", "general")
        
        # 根据问题类型确定回答策略
        strategies = {
            "self_intro": "使用结构化的自我介绍模板",
            "project_experience": "使用STAR法则组织项目经历",
            "technical": "先讲原理，再讲实践，最后总结",
            "behavioral": "使用STAR法则描述具体场景",
            "salary": "表达合理期望，强调价值匹配",
            "qa": "提出有深度的问题展示思考",
            "general": "清晰、简洁、有条理地回答"
        }
        
        strategy = strategies.get(phase, strategies["general"])
        
        thinking = {
            "step": "组织回答",
            "status": "completed",
            "detail": f"回答策略: {strategy}"
        }
        
        return {
            "thinking_process": state.get("thinking_process", []) + [thinking]
        }
    
    def _generate_response(self, state: InterviewState) -> Dict:
        """生成面试者回答"""
        
        # 创建LLM
        if state.get("llm_config"):
            llm = llm_factory.create_llm(state["llm_config"])
        else:
            # 使用默认配置
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        
        # 构建系统Prompt（面试者角色）
        system_prompt = self._build_system_prompt(state)
        
        # 构建消息列表
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        
        # 调用LLM生成回答
        response = llm.invoke(messages)
        
        thinking = {
            "step": "生成回答",
            "status": "completed",
            "detail": "回答生成完成"
        }
        
        return {
            "messages": [AIMessage(content=response.content)],
            "thinking_process": state.get("thinking_process", []) + [thinking]
        }
    
    def _build_system_prompt(self, state: InterviewState) -> str:
        """构建系统Prompt（面试者角色）"""
        
        resume = state.get("resume_data", {})
        job = state.get("job_info", {})
        phase = state.get("current_phase", "general")
        
        # 基础角色定义
        prompt = f"""你是一位正在求职的候选人，正在参加一场真实的面试。你需要根据面试官的问题，结合你的简历和知识库内容，给出专业、真实、有说服力的回答。

## 你的简历信息
{json.dumps(resume, ensure_ascii=False, indent=2)}

## 应聘岗位信息
{json.dumps(job, ensure_ascii=False, indent=2)}

## 当前面试阶段
{phase}

## 回答要求
1. 保持谦逊、自信、专业的态度
2. 回答要具体、有数据支撑、避免空泛
3. 不懂的问题诚实承认，不要编造
4. 展现学习能力和解决问题的思路
5. 根据面试岗位调整回答的侧重点
"""
        
        # 根据阶段添加特定指导
        if phase == "self_intro":
            prompt += """
## 自我介绍指导
- 结构：姓名 → 教育背景 → 工作经历 → 核心技能 → 应聘动机
- 时长：2-3分钟
- 突出与岗位相关的经验和成就
"""
        elif phase == "project_experience":
            prompt += """
## 项目经历回答指导（必须使用STAR法则）
- S (Situation): 项目背景是什么？
- T (Task): 你的具体任务是什么？
- A (Action): 你采取了哪些行动？
- R (Result): 最终取得了什么成果？（必须有量化数据）
"""
        elif phase == "technical":
            prompt += """
## 技术问题回答指导
- 先讲原理和概念
- 再讲实际应用和经验
- 最后总结和反思
- 可以对比不同方案的优缺点
"""
        
        return prompt
    
    async def chat(self, session_id: str, user_id: str, message: str, 
                   resume_data: Dict = None, job_info: Dict = None,
                   history: List[Dict] = None) -> Dict:
        """
        处理面试对话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            message: 面试官的问题
            resume_data: 简历数据
            job_info: 岗位信息
            history: 对话历史
            
        Returns:
            Dict: 包含回答和思考过程
        """
        # 构建消息列表
        messages = []
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # 添加当前问题
        messages.append(HumanMessage(content=message))
        
        # 构建初始状态
        initial_state = {
            "messages": messages,
            "session_id": session_id,
            "user_id": user_id,
            "current_phase": "general",
            "resume_data": resume_data or {},
            "job_info": job_info or {},
            "knowledge_context": [],
            "thinking_process": [],
            "llm_config": self.llm_config
        }
        
        # 执行工作流
        result = self.workflow.invoke(initial_state)
        
        # 提取最后一条AI消息
        ai_message = None
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                ai_message = msg.content
                break
        
        return {
            "response": ai_message,
            "thinking_process": result.get("thinking_process", []),
            "current_phase": result.get("current_phase", "general")
        }


# 全局Agent实例
interview_agent = InterviewAgent()
