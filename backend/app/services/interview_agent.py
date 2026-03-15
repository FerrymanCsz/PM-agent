"""
面试Agent核心 - LangGraph工作流实现
用户是面试官,Agent是面试者
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
from app.services.vector_index import vector_index_manager
from app.models.database import LLMConfig
from app.core.config import settings


class ConversationRound(TypedDict):
    """对话轮次"""
    round_number: int  # 轮次编号
    question: str  # 面试官问题
    full_response: str  # 候选人完整回答
    summary: str  # 对话摘要


class InterviewState(TypedDict):
    """面试状态定义"""
    messages: Annotated[List[BaseMessage], operator.add]  # 对话历史(LangChain消息格式)
    session_id: str  # 会话ID
    user_id: str  # 用户ID
    current_phase: str  # 当前面试阶段
    resume_data: Dict  # 简历数据
    job_info: Dict  # 岗位信息
    knowledge_context: List[str]  # 知识库上下文
    thinking_process: List[Dict]  # 思考过程(用于可视化)
    llm_config: Optional[LLMConfig]  # LLM配置
    conversation_history: List[ConversationRound]  # 对话历史摘要(用于上下文)


class InterviewAgent:
    """面试Agent - 扮演面试者角色"""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config
        self.workflow = self._build_workflow()
        # 引入向量索引管理器
        self.vector_manager = vector_index_manager
    
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
        
        # 获取最后一条用户消息(面试官的问题)
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
        """增强的知识检索(同时检索简历和知识库)"""

        # 获取查询
        last_message = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_message = msg.content
                break

        resume_data = state.get("resume_data", {})
        resume_id = resume_data.get("id", "default")
        phase = state.get("current_phase", "general")

        all_context = []
        resume_results = []
        knowledge_results = []

        # 1. 检索相关简历内容
        try:
            resume_results = self.vector_manager.search_resume(
                query=last_message,
                resume_id=resume_id,
                question_type=phase,
                top_k=2
            )
            all_context.extend([
                f"[简历-{r['type']}] {r['content']}"
                for r in resume_results
            ])
        except Exception as e:
            print(f"简历检索失败: {e}")

        # 2. 检索知识库(使用混合检索:向量 + BM25 + RRF融合)
        try:
            knowledge_results = self.vector_manager.search_knowledge(
                query=last_message,
                source_type="knowledge",  # 只搜索手动上传的知识库
                top_k=5,
                use_fusion=True,  # 启用混合检索
                fusion_method="rrf"
            )
            
            # 格式化知识库结果(适配混合检索新格式)
            for r in knowledge_results:
                header_path = r.get('header_path', '')
                section = r.get('section', '')
                content = r['content']  # 不截断,保留完整内容
                sources = r.get('sources', ['vector'])  # 来源列表
                
                # 构建上下文标识
                context_label = f"[知识库-{r['category']}]"
                
                # 添加来源信息
                if len(sources) > 1:
                    source_str = '+'.join(sources)
                    context_label += f"[{source_str}]"
                
                if header_path:
                    context_label += f"[{header_path}]"
                elif section:
                    context_label += f"[{section}]"
                
                all_context.append(f"{context_label} {content}")
                
        except Exception as e:
            print(f"知识库检索失败: {e}")

        # 统计混合检索来源分布
        vector_count = sum(1 for r in knowledge_results if 'vector' in r.get('sources', []))
        bm25_count = sum(1 for r in knowledge_results if 'bm25' in r.get('sources', []))
        fusion_count = sum(1 for r in knowledge_results if len(r.get('sources', [])) > 1)
        
        thinking = {
            "step": "知识检索",
            "status": "completed",
            "detail": f"简历: {len(resume_results)} 条 | 知识库: {len(knowledge_results)} 条 (向量:{vector_count} BM25:{bm25_count} 融合:{fusion_count})",
            "sources": [r.get('type') for r in resume_results] + [r.get('category') for r in knowledge_results]
        }

        return {
            "knowledge_context": all_context,
            "thinking_process": state.get("thinking_process", []) + [thinking]
        }
    
    def _organize_answer(self, state: InterviewState) -> Dict:
        """组织回答结构"""
        
        phase = state.get("current_phase", "general")
        
        # 根据问题类型确定回答策略
        strategies = {
            "self_intro": "使用结构化的自我介绍模板",
            "project_experience": "使用STAR法则组织项目经历",
            "technical": "先讲原理,再讲实践,最后总结",
            "behavioral": "使用STAR法则描述具体场景",
            "salary": "表达合理期望,强调价值匹配",
            "qa": "提出有深度的问题展示思考",
            "general": "清晰,简洁,有条理地回答"
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
    
    async def _generate_response(self, state: InterviewState) -> Dict:
        """生成面试者回答(异步版本)"""
        import asyncio
        from langchain_openai import ChatOpenAI
        
        # 创建LLM
        if state.get("llm_config"):
            print(f"[DEBUG] Using llm_config from state: model={state['llm_config'].model}, temp={state['llm_config'].temperature}")
            llm = llm_factory.create_llm(state["llm_config"])
        else:
            # 使用默认配置(从settings读取)
            api_key = settings.DEFAULT_LLM_API_KEY
            base_url = settings.DEFAULT_LLM_BASE_URL
            model = settings.DEFAULT_LLM_MODEL
            
            if not api_key:
                # 如果没有配置API key,返回错误提示
                return {
                    "messages": [AIMessage(content="抱歉,服务暂时不可用,请稍后重试.错误:未配置LLM API Key")],
                    "thinking_process": state.get("thinking_process", []) + [{
                        "step": "生成回答",
                        "status": "error",
                        "detail": "未配置LLM API Key"
                    }]
                }
            
            # 检测是否为 Kimi/Moonshot 模型
            model_lower = model.lower()
            is_kimi = "kimi" in model_lower or "moonshot" in model_lower
            
            # 构建参数
            llm_params = {
                "model": model,
                "api_key": api_key,
                "base_url": base_url,
            }
            
            # 对于 Kimi/Moonshot 模型,必须显式设置 temperature=1(使用整数)
            if is_kimi:
                llm_params["temperature"] = 1  # 使用整数 1 而不是 1.0
                print(f"[DEBUG] Kimi/Moonshot model in interview_agent, setting temperature=1")
            else:
                llm_params["temperature"] = 0.7
            
            print(f"[DEBUG] Creating ChatOpenAI with params: {llm_params}")
            llm = ChatOpenAI(**llm_params)
        
        # 构建系统Prompt(面试者角色)
        system_prompt = self._build_system_prompt(state)
        
        # 构建消息列表
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        
        # 在后台线程中调用LLM(避免阻塞事件循环)
        # 添加重试机制处理429错误
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: llm.invoke(messages))
                break  # 成功则跳出循环
            except Exception as e:
                error_msg = str(e)
                
                # 检查是否是429错误或引擎过载错误
                if "429" in error_msg or "overloaded" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"[WARN] LLM服务过载 (尝试 {attempt + 1}/{max_retries}),{retry_delay}秒后重试...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                        continue
                
                # 其他错误或重试耗尽
                return {
                    "messages": [AIMessage(content=f"抱歉,生成回答时出错:{error_msg}.请稍后重试.")],
                    "thinking_process": state.get("thinking_process", []) + [{
                        "step": "生成回答",
                        "status": "error",
                        "detail": f"LLM调用失败: {error_msg}"
                    }]
                }
        
        # 解析LLM输出(JSON格式)
        import json
        raw_content = response.content.strip()
        full_response = raw_content
        summary = ""
        
        try:
            # 尝试提取JSON内容
            json_content = raw_content.strip()
            
            # 尝试直接解析(LLM可能直接输出JSON)
            try:
                parsed = json.loads(json_content)
                full_response = parsed.get("response", raw_content)
                summary = parsed.get("summary", "")
            except json.JSONDecodeError:
                # 如果直接解析失败,尝试提取代码块
                if "```json" in raw_content:
                    start = raw_content.find("```json") + 7
                    end = raw_content.find("```", start)
                    if end > start:
                        json_content = raw_content[start:end].strip()
                elif "```" in raw_content:
                    start = raw_content.find("```") + 3
                    end = raw_content.find("```", start)
                    if end > start:
                        json_content = raw_content[start:end].strip()
                
                # 再次解析
                parsed = json.loads(json_content)
                full_response = parsed.get("response", raw_content)
                summary = parsed.get("summary", "")
            
        except json.JSONDecodeError as e:
            print(f"[WARN] JSON解析失败,使用原始内容: {e}")
            print(f"[DEBUG] 原始内容前100字: {raw_content[:100]}")
            # 降级处理:使用原始内容
            full_response = raw_content
            summary = raw_content[:200] + "..." if len(raw_content) > 200 else raw_content
        except Exception as e:
            print(f"[WARN] 解析LLM输出失败: {e}")
            full_response = raw_content
            summary = raw_content[:200] + "..." if len(raw_content) > 200 else raw_content
        
        thinking = {
            "step": "生成回答",
            "status": "completed",
            "detail": f"回答生成完成,长度: {len(full_response)} 字符,摘要: {len(summary)} 字符"
        }
        
        return {
            "messages": [AIMessage(content=full_response)],  # 只返回完整回答给用户
            "full_response": full_response,  # 完整回答
            "summary": summary,  # 对话摘要
            "thinking_process": state.get("thinking_process", []) + [thinking]
        }
    
    def _build_conversation_history(self, state: InterviewState, max_rounds: int = 5) -> str:
        """构建对话历史(摘要形式)"""
        conversation_history = state.get("conversation_history", [])
        
        if not conversation_history:
            return "(对话刚开始,暂无历史)"
        
        # 只取最近N轮
        recent_history = conversation_history[-max_rounds:] if len(conversation_history) > max_rounds else conversation_history
        
        lines = ["## 对话历史(按时间顺序)"]
        for round_data in recent_history:
            round_num = round_data.get("round_number", 0)
            question = round_data.get("question", "")
            summary = round_data.get("summary", "")
            lines.append(f"\n第{round_num}轮:")
            lines.append(f"  面试官: {question}")
            lines.append(f"  候选人: {summary}")
        
        return "\n".join(lines)
    
    def _build_system_prompt(self, state: InterviewState) -> str:
        """构建系统Prompt(使用向量检索的简历上下文)"""

        job = state.get("job_info", {})
        phase = state.get("current_phase", "general")
        resume_data = state.get("resume_data", {})
        resume_id = resume_data.get("id", "default")
        knowledge_context = state.get("knowledge_context", [])

        # 获取最后一条用户消息
        last_message = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_message = msg.content
                break

        # 使用向量检索获取相关简历上下文(替代完整的简历JSON)
        try:
            resume_context = self.vector_manager.get_resume_prompt_context(
                resume_id=resume_id,
                query=last_message,
                question_type=phase,
                max_length=2000
            )
        except Exception as e:
            print(f"获取简历上下文失败: {e}")
            # 降级处理:使用简化版简历信息
            resume_context = f"""姓名: {resume_data.get('name', '未知')}
职位: {resume_data.get('title', '未知')}
技能: {', '.join(resume_data.get('skills', [])[:10])}"""

        # 构建知识库上下文部分(混合检索结果:向量 + BM25 + RRF融合)
        knowledge_section = ""
        if knowledge_context:
            knowledge_section = "\n## 相关知识库内容(检索到的参考资料)\n"
            for i, ctx in enumerate(knowledge_context, 1):  # 显示所有召回的结果
                knowledge_section += f"{ctx}\n\n"

        # 构建精简的系统Prompt
        prompt = f"""# 角色设定
你是一位正在求职的候选人,正在参加一场真实的面试.请根据以下信息回答问题.

---

# 一,应聘岗位
- **公司**: {job.get('company', '未知')}
- **职位**: {job.get('position', '未知')}
- **部门**: {job.get('department', '未知')}
- **岗位要求**: {', '.join(job.get('requirements', [])[:5]) if job.get('requirements') else '无特殊要求'}

---

# 二,你的简历信息
{resume_context}

---

# 三,参考资料
{knowledge_section if knowledge_section else '(无额外参考资料)'}

---

# 四,当前面试阶段
**{phase}**

---

# 五,面试官的问题
**{last_message}**

---

# 六,回答要求
## 基本原则
1. 保持谦逊,自信,专业的态度
2. 回答要具体,有数据支撑,避免空泛
3. 不懂的问题诚实承认,不要编造
4. 必须基于简历信息回答,不要编造简历中没有的数据
5. 展现学习能力和解决问题的思路
6. 根据面试岗位调整回答侧重点

## 阶段-specific指导
{self._get_phase_guidance(phase)}

---

# 七,输出格式(极其重要)
你必须严格按以下JSON格式输出,不要输出任何其他内容:

```json
{{
  "response": "你的完整面试回答,自然口语化,200-400字",
  "summary": "问题要点;核心数据;关键逻辑;结论"
}}
```

**严格要求**:
- 只输出JSON,不要有markdown代码块标记
- response:完整回答内容
- summary:用分号分隔4个要素
- 示例:`{{"response": "面试官您好...", "summary": "问题:自我介绍;数据:2年经验;逻辑:背景->能力->动机;结论:期待加入"}}`
"""
        
        return prompt
    
    def _get_phase_guidance(self, phase: str) -> str:
        """获取阶段特定的回答指导"""
        guidance_map = {
            "self_intro": """**自我介绍**
- 结构: 姓名 -> 教育背景 -> 工作经历 -> 核心技能 -> 应聘动机
- 时长: 2-3分钟
- 突出与岗位相关的经验和成就""",
            
            "project_experience": """**项目经历 (STAR法则)**
- S (Situation): 项目背景是什么?
- T (Task): 你的具体任务是什么?
- A (Action): 你采取了哪些行动?
- R (Result): 最终取得了什么成果? (必须有量化数据)""",
            
            "technical": """**技术问题**
- 先讲原理和概念
- 再讲实际应用和经验
- 最后总结和反思
- 可以对比不同方案的优缺点""",
            
            "behavioral": """**行为问题**
- 使用STAR法则描述具体情境
- 强调你的行动和决策过程
- 突出团队协作和沟通能力""",
            
            "career_planning": """**职业规划**
- 短期目标(1-2年): 技能提升,岗位适应
- 中期目标(3-5年): 专业深耕,团队贡献
- 长期目标(5年以上): 与公司和岗位结合""",
            
            "salary": """**薪资期望**
- 先了解公司薪资结构
- 给出合理范围而非具体数字
- 强调更看重发展机会""",
            
            "general": """**通用问题**
- 保持真诚和积极的态度
- 结合简历中的具体经历
- 展现对岗位和公司的了解"""
        }
        
        return guidance_map.get(phase, guidance_map["general"])
    
    def _should_retrieve_knowledge(self, question_type: str, question: str) -> bool:
        """判断是否需要检索知识库"""
        # 技术问题需要检索
        if question_type == "technical":
            return True
        # 项目经验问题需要检索
        if question_type == "project_experience":
            return True
        # 自我介绍需要检索
        if question_type == "self_intro":
            return True
        # 行为问题需要检索
        if question_type == "behavioral":
            return True
        return False
    
    async def chat(self, session_id: str, user_id: str, message: str, 
                   resume_data: Dict = None, job_info: Dict = None,
                   history: List[Dict] = None) -> Dict:
        """
        处理面试对话(异步版本)- 动态规划步骤
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            message: 面试官的问题
            resume_data: 简历数据
            job_info: 岗位信息
            history: 对话历史
            
        Returns:
            Dict: 包含回答,思考过程和监控数据
        """
        import time
        start_time = time.time()
        step_durations = {}
        
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
        
        # 从历史中提取对话摘要列表
        conversation_history = []
        if history:
            for i, msg in enumerate(history):
                if msg.get("role") == "assistant":
                    # 找到对应的用户问题
                    question = ""
                    if i > 0 and history[i-1].get("role") == "user":
                        question = history[i-1].get("content", "")
                    
                    # 获取摘要,如果没有摘要则用完整内容的前200字
                    summary = msg.get("summary", "")
                    if not summary and msg.get("content"):
                        summary = msg.get("content", "")[:200] + "..."
                    
                    if summary:  # 只有有内容才添加
                        conversation_history.append({
                            "round_number": len(conversation_history) + 1,
                            "question": question,
                            "full_response": msg.get("content", ""),
                            "summary": summary
                        })
        
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
            "llm_config": self.llm_config,
            "conversation_history": conversation_history
        }
        
        # 步骤1: 理解问题(必须)
        step_start = time.time()
        result1 = self._understand_question(initial_state)
        step_durations["understand_question"] = (time.time() - step_start) * 1000
        current_state = {**initial_state, **result1}
        question_type = current_state.get("current_phase", "general")
        
        # 动态决定后续步骤
        executed_steps = ["understand_question"]
        
        # 步骤2: 知识检索(可选)- 根据问题类型决定
        step_start = time.time()
        if self._should_retrieve_knowledge(question_type, message):
            result2 = self._retrieve_knowledge(current_state)
            current_state = {**current_state, **result2}
            executed_steps.append("retrieve_knowledge")
        else:
            # 添加跳过的思考记录
            thinking = {
                "step": "知识检索",
                "status": "skipped",
                "detail": f"问题类型 '{question_type}' 不需要知识库检索"
            }
            current_state["thinking_process"] = current_state.get("thinking_process", []) + [thinking]
        step_durations["retrieve_knowledge"] = (time.time() - step_start) * 1000
        
        # 步骤3: 组织回答(必须)
        step_start = time.time()
        result3 = self._organize_answer(current_state)
        current_state = {**current_state, **result3}
        executed_steps.append("organize_answer")
        step_durations["organize_answer"] = (time.time() - step_start) * 1000
        
        # 步骤4: 生成回答(必须)
        step_start = time.time()
        result4 = await self._generate_response(current_state)
        current_state = {**current_state, **result4}
        executed_steps.append("generate_response")
        step_durations["generate_response"] = (time.time() - step_start) * 1000
        
        # 计算总耗时
        total_duration = (time.time() - start_time) * 1000
        
        # 记录执行的步骤
        print(f"[InterviewAgent] 问题类型: {question_type}, 执行步骤: {executed_steps}, 总耗时: {total_duration:.2f}ms")
        
        # 提取最后一条AI消息和摘要
        ai_message = None
        raw_response = ""
        full_response = ""
        summary = ""
        for msg in reversed(result4.get("messages", [])):
            if isinstance(msg, AIMessage):
                ai_message = msg.content
                raw_response = msg.content
                break
        
        # 获取完整回答和摘要
        full_response = result4.get("full_response", raw_response)
        summary = result4.get("summary", "")
        
        # 构建系统提示词(用于监控)
        system_prompt = self._build_system_prompt(current_state)
        
        # 构建监控数据
        monitor_data = {
            "input": {
                "user_message": message,
                "resume_data": resume_data or {},
                "job_info": job_info or {},
                "history": history or []
            },
            "prompt": {
                "system_prompt": system_prompt,
                "full_messages": [{"role": "system", "content": system_prompt}] + 
                                [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} 
                                 for m in messages],
                "model": self.llm_config.model if self.llm_config else settings.DEFAULT_LLM_MODEL,
                "temperature": 1.0
            },
            "output": {
                "raw_response": raw_response,
                "full_response": full_response,
                "summary": summary,
                "question": message,
                "thinking_process": current_state.get("thinking_process", []),
                "parsed_response": ai_message
            },
            "stats": {
                "start_time": start_time,
                "end_time": time.time(),
                "duration_ms": total_duration,
                "step_durations": step_durations
            }
        }
        
        return {
            "response": ai_message,
            "thinking_process": current_state.get("thinking_process", []),
            "current_phase": current_state.get("current_phase", "general"),
            "executed_steps": executed_steps,
            "monitor_data": monitor_data,
            "summary": summary  # 将摘要提取到顶层
        }


# 全局Agent实例
interview_agent = InterviewAgent()
