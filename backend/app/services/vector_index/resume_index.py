"""
简历向量索引

提供简历的智能分块和向量索引功能。
"""
from typing import List, Dict, Any, Optional
from .base import BaseVectorIndex, IndexDocument, SearchResult


class ResumeIndex(BaseVectorIndex):
    """简历向量索引"""

    def __init__(self, db_path: str = "./chroma_db"):
        super().__init__("resume_chunks", db_path)

    def chunk_document(self, resume_data: Dict) -> List[IndexDocument]:
        """
        简历分块策略
        将简历按模块拆分，每个模块独立索引
        """
        chunks = []
        resume_id = resume_data.get("id", "unknown")

        # 1. 基本信息块
        # 从最近的工作经历中提取职位作为 title
        experience = resume_data.get("experience", [])
        latest_position = experience[0].get("position", "") if experience else ""
        
        basic_info = {
            "name": resume_data.get("name", ""),
            "title": latest_position,
            "summary": resume_data.get("summary", ""),
            "email": resume_data.get("email", ""),
            "phone": resume_data.get("phone", ""),
        }
        chunks.append(IndexDocument(
            id=f"{resume_id}_basic",
            content=self._format_basic_info(basic_info),
            metadata={
                "resume_id": resume_id,
                "chunk_type": "basic_info",
                "chunk_index": 0,
                "source_field": "basic",
                "name": basic_info.get("name", ""),
                "title": basic_info.get("title", "")
            }
        ))

        # 2. 教育经历块（每条一个）
        for idx, edu in enumerate(resume_data.get("education", [])):
            chunks.append(IndexDocument(
                id=f"{resume_id}_edu_{idx}",
                content=self._format_education(edu),
                metadata={
                    "resume_id": resume_id,
                    "chunk_type": "education",
                    "chunk_index": idx,
                    "school": edu.get("school", ""),
                    "degree": edu.get("degree", ""),
                    "source_field": f"education.{idx}"
                }
            ))

        # 3. 工作经历块（每条一个）
        for idx, exp in enumerate(resume_data.get("experience", [])):
            chunks.append(IndexDocument(
                id=f"{resume_id}_exp_{idx}",
                content=self._format_experience(exp),
                metadata={
                    "resume_id": resume_id,
                    "chunk_type": "experience",
                    "chunk_index": idx,
                    "company": exp.get("company", ""),
                    "position": exp.get("position", ""),
                    "duration": exp.get("duration", ""),
                    "source_field": f"experience.{idx}"
                }
            ))

        # 4. 项目经验块（每条一个）
        for idx, proj in enumerate(resume_data.get("projects", [])):
            chunks.append(IndexDocument(
                id=f"{resume_id}_proj_{idx}",
                content=self._format_project(proj),
                metadata={
                    "resume_id": resume_id,
                    "chunk_type": "project",
                    "chunk_index": idx,
                    "project_name": proj.get("name", ""),
                    "technologies": ",".join(proj.get("technologies", [])),
                    "source_field": f"projects.{idx}"
                }
            ))

        # 5. 技能块（每10个技能一块）
        skills = resume_data.get("skills", [])
        if skills:
            skill_chunks = self._chunk_skills(skills, resume_id)
            chunks.extend(skill_chunks)

        return chunks

    def _format_basic_info(self, basic: Dict) -> str:
        """格式化基本信息"""
        return f"""姓名: {basic.get('name', '未知')}
职位: {basic.get('title', '未知')}
个人简介: {basic.get('summary', '暂无')}
联系方式: {basic.get('email', '')} {basic.get('phone', '')}""".strip()

    def _format_education(self, edu: Dict) -> str:
        """格式化教育经历"""
        return f"""教育经历:
学校: {edu.get('school', '未知')}
专业: {edu.get('major', '未知')}
学位: {edu.get('degree', '未知')}
时间: {edu.get('start_date', '未知')} - {edu.get('end_date', '未知')}
描述: {edu.get('description', '无')}""".strip()

    def _format_experience(self, exp: Dict) -> str:
        """格式化工作经历"""
        # 处理时间
        start_date = exp.get('start_date', '未知')
        end_date = exp.get('end_date', '未知')
        duration = f"{start_date} - {end_date}" if start_date != '未知' else '未知'
        
        return f"""工作经历:
公司: {exp.get('company', '未知')}
职位: {exp.get('position', '未知')}
部门: {exp.get('department', '未知')}
时间: {duration}
职责描述: {exp.get('description', exp.get('responsibilities', '无'))}""".strip()

    def _format_project(self, proj: Dict) -> str:
        """格式化项目经验"""
        # 处理技术栈：可能是列表或字符串
        technologies = proj.get('technologies', [])
        if isinstance(technologies, list):
            tech_str = ', '.join(technologies)
        else:
            tech_str = str(technologies) if technologies else '无'
        
        return f"""项目经验:
项目名称: {proj.get('name', '未知')}
角色: {proj.get('role', '未知')}
时间: {proj.get('duration', '未知')}
描述: {proj.get('description', '无')}
技术栈: {tech_str}
个人贡献: {proj.get('contributions', proj.get('contribution', '无'))}
项目成果: {proj.get('results', proj.get('achievements', '无'))}""".strip()

    def _chunk_skills(self, skills: List[str], resume_id: str) -> List[IndexDocument]:
        """技能分块（每10个技能一块）"""
        chunks = []
        chunk_size = 10

        for i in range(0, len(skills), chunk_size):
            chunk_skills = skills[i:i + chunk_size]
            chunks.append(IndexDocument(
                id=f"{resume_id}_skills_{i // chunk_size}",
                content=f"技能列表: {', '.join(chunk_skills)}",
                metadata={
                    "resume_id": resume_id,
                    "chunk_type": "skills",
                    "chunk_index": i // chunk_size,
                    "skills": ",".join(chunk_skills),
                    "source_field": f"skills.{i // chunk_size}"
                }
            ))

        return chunks

    def build_index(self, resume_id: str, resume_data: Dict) -> List[str]:
        """构建简历索引"""
        # 先删除旧索引
        self.delete_by_filter({"resume_id": {"$eq": resume_id}})

        # 分块并索引
        chunks = self.chunk_document({**resume_data, "id": resume_id})
        return self.add_documents(chunks)

    def search_relevant(
        self,
        query: str,
        resume_id: str,
        top_k: int = 3,
        chunk_types: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        搜索简历相关内容

        Args:
            query: 查询问题
            resume_id: 简历ID
            top_k: 返回结果数
            chunk_types: 指定搜索的块类型（如 ["project", "experience"]）
        """
        # ChromaDB 0.5.x 的 where 语法需要使用 $eq 操作符
        filter_dict = {"resume_id": {"$eq": resume_id}}

        if chunk_types:
            # ChromaDB不支持直接IN查询，需要多次查询后合并
            all_results = []
            for chunk_type in chunk_types:
                type_filter = {
                    "$and": [
                        {"resume_id": {"$eq": resume_id}},
                        {"chunk_type": {"$eq": chunk_type}}
                    ]
                }
                results = self.search(query, type_filter, top_k)
                all_results.extend(results)

            # 按分数排序并返回top_k
            all_results.sort(key=lambda x: x.score, reverse=True)
            return all_results[:top_k]

        return self.search(query, filter_dict, top_k)

    def get_resume_summary(self, resume_id: str) -> Dict[str, Any]:
        """获取简历摘要（用于提示词）"""
        # 从元数据中提取简历结构
        try:
            results = self.collection.get(
                where={"resume_id": {"$eq": resume_id}},
                include=["metadatas"]
            )
        except Exception as e:
            print(f"获取简历摘要失败: {e}")
            return {
                "basic_info": {},
                "education_count": 0,
                "experience_count": 0,
                "project_count": 0,
                "skills": []
            }

        summary = {
            "basic_info": {},
            "education_count": 0,
            "experience_count": 0,
            "project_count": 0,
            "skills": []
        }

        if not results or not results.get("metadatas"):
            return summary

        for metadata in results["metadatas"]:
            chunk_type = metadata.get("chunk_type")

            if chunk_type == "basic_info":
                summary["basic_info"] = {
                    "name": metadata.get("name", ""),
                    "title": metadata.get("title", "")
                }
            elif chunk_type == "education":
                summary["education_count"] += 1
            elif chunk_type == "experience":
                summary["experience_count"] += 1
            elif chunk_type == "project":
                summary["project_count"] += 1
            elif chunk_type == "skills":
                skills_str = metadata.get("skills", "")
                if skills_str:
                    summary["skills"].extend(skills_str.split(","))

        return summary
