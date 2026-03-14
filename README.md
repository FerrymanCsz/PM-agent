# 面试模拟Agent系统

一个面向面试官的面试模拟系统，Agent扮演求职者角色，帮助面试官练习面试技巧、测试面试问题。

## 核心角色

- **用户（您）**: 面试官，负责提问
- **Agent**: 面试者，基于简历和知识库回答问题

## 技术栈

### 后端
- **FastAPI**: Web框架
- **LangGraph + LangChain**: Agent工作流
- **ChromaDB**: 向量数据库
- **SQLite**: 关系数据库

### 前端
- **React 18**: UI框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具
- **Ant Design**: UI组件库

## 环境要求

### 必需环境
- **Node.js**: >= 18.0.0
- **Python**: >= 3.11
- **包管理器**: npm 或 yarn

### 可选工具
- **Miniconda/Anaconda**: 用于Python环境管理（推荐）
- **Git**: 版本控制

## 快速开始

### 方式一：使用 Miniconda（推荐）

#### 1. 安装 Miniconda

下载并安装 Miniconda：
```bash
# Windows
# 下载 miniconda.exe 并运行安装程序
# 或使用项目自带的 miniconda.exe
.\miniconda.exe /S /D=D:\trae\PM_agent\miniconda3
```

#### 2. 创建Python环境

```bash
# 使用 miniconda 创建环境
cd d:\trae\PM_agent
miniconda3\_conda.exe create -n interview_agent python=3.11 -y

# 激活环境
miniconda3\Scripts\activate.bat interview_agent
```

#### 3. 安装后端依赖

```bash
cd backend
pip install fastapi uvicorn sqlalchemy aiosqlite python-multipart sse-starlette python-dotenv pydantic-settings
pip install langgraph langchain langchain-openai langchain-anthropic langchain-community
pip install chromadb python-docx duckduckgo-search httpx aiofiles
```

#### 4. 安装前端依赖

```bash
cd frontend
npm install
```

### 方式二：使用本地Python

#### 1. 检查Python版本

```bash
python --version  # 需要 3.11+
```

#### 2. 创建虚拟环境（可选但推荐）

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 安装前端依赖

```bash
cd frontend
npm install
```

## 启动服务

### 使用启动脚本（Windows）

```bash
# 启动后端（会自动创建虚拟环境并安装依赖）
.\start_backend.bat
```

### 手动启动

#### 启动后端（端口5000）

```bash
cd backend

# 使用 miniconda Python
D:\trae\PM_agent\miniconda3\python.exe run.py

# 或使用本地 Python
python run.py
```

#### 启动前端（端口3000）

```bash
cd frontend
npm run dev
```

### 4. 访问应用

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:5000
- **API文档**: http://localhost:5000/docs

## 配置环境变量

在 `backend` 目录下创建 `.env` 文件：

```env
# 应用配置
DEBUG=true
HOST=0.0.0.0
PORT=5000

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./interview_agent.db

# ChromaDB配置
CHROMA_DB_PATH=./chroma_db

# 知识库路径
KNOWLEDGE_BASE_PATH=./knowledge_base

# 上传文件配置
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 默认LLM配置（可选，用户可以在界面配置自己的）
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4o-mini
DEFAULT_LLM_BASE_URL=https://api.openai.com/v1
DEFAULT_LLM_API_KEY=your-api-key-here
```

## 项目结构

```
.
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   │   ├── chat.py              # 聊天接口
│   │   │   ├── llm_config.py        # LLM配置
│   │   │   ├── resume.py            # 简历管理
│   │   │   ├── job.py               # 岗位配置
│   │   │   └── knowledge.py         # 知识库管理
│   │   ├── core/           # 核心配置
│   │   │   └── config.py
│   │   ├── models/         # 数据库模型
│   │   │   └── database.py
│   │   ├── services/       # 业务逻辑
│   │   │   ├── llm_factory.py       # LLM工厂
│   │   │   ├── resume_parser.py     # 简历解析
│   │   │   ├── interview_agent.py   # Agent核心
│   │   │   └── vector_index/        # 向量索引
│   │   │       ├── base.py
│   │   │       ├── knowledge_index.py
│   │   │       ├── resume_index.py
│   │   │       └── manager.py
│   │   └── main.py         # 应用入口
│   ├── requirements.txt
│   └── run.py
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # 公共组件
│   │   │   ├── ChatMonitor.tsx
│   │   │   ├── ExperienceCard.tsx
│   │   │   ├── LLMConfigModal.tsx
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── ResumeUploader.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── pages/          # 页面
│   │   │   ├── ChatPage.tsx         # 面试对话
│   │   │   ├── ResumePage.tsx       # 简历管理
│   │   │   ├── JobPage.tsx          # 岗位配置
│   │   │   ├── LLMConfigPage.tsx    # LLM配置
│   │   │   └── KnowledgePage.tsx    # 知识库管理
│   │   ├── App.tsx         # 主应用
│   │   ├── main.tsx        # 入口
│   │   └── index.css
│   ├── index.html
│   └── package.json
├── docs/                   # 文档
│   ├── 00_调研总结.md
│   ├── 01_需求规格说明书.md
│   ├── 02_技术方案文档.md
│   ├── 03_系统架构图.md
│   ├── 04_界面原型设计.md
│   └── 05_Prompt设计方案.md
├── knowledge_base/         # 知识库文件
├── miniconda.exe           # Miniconda安装包（Windows）
├── start_backend.bat       # 后端启动脚本
├── start_services.bat      # 一键启动前后端
├── INSTALL.md             # 详细安装指南
└── README.md              # 项目说明
```

## 核心功能

### 1. LLM可配置
- 支持 OpenAI、Anthropic、DeepSeek、OpenRouter 等
- 用户可以配置自己的 Base URL 和 API Key
- 支持多配置切换

### 2. 简历管理
- 上传 Word 格式简历
- 自动解析结构化信息
- 简历向量化索引
- Agent以此身份回答

### 3. 知识库管理
- 支持 Markdown 格式文档上传
- 智能分块策略（按标题层级分割）
- 自动向量嵌入（ChromaDB）
- 支持多级标题结构（1-6级）
- 面试时自动检索相关内容

**知识库元数据：**
- `source_type`: knowledge(手动上传) / resume(简历生成)
- `knowledge_type`: technical / behavioral / career / general
- `category`: 技术分类（backend/frontend/ai等）

### 4. 岗位配置
- 配置目标岗位信息
- 设置面试重点和要求
- Agent根据岗位调整回答策略

### 5. 面试对话
- 流式输出（SSE）
- 思考过程可视化
- 支持多轮对话
- 对话历史保存
- 监控数据记录

## API接口

### 聊天接口

```bash
# 非流式接口
POST /api/v1/chat/message
{
    "message": "请先做个自我介绍",
    "resume_data": {...},
    "job_info": {...}
}

# 流式接口（SSE）
POST /api/v1/chat/stream
{
    "message": "能说说你的项目经验吗？",
    "resume_data": {...},
    "job_info": {...}
}

# 获取监控数据
GET /api/v1/chat/monitor/{session_id}
```

### 简历接口

```bash
# 上传简历
POST /api/v1/resumes/upload

# 获取简历列表
GET /api/v1/resumes/list

# 获取当前简历
GET /api/v1/resumes/current

# 切换当前简历
POST /api/v1/resumes/{resume_id}/activate
```

### 知识库接口

```bash
# 创建文档
POST /api/v1/knowledge/docs
{
    "title": "Redis缓存设计",
    "content": "## 缓存穿透...",
    "category": "backend",
    "knowledge_type": "technical"
}

# 获取文档列表
GET /api/v1/knowledge/docs?page=1&category=backend

# 获取文档详情
GET /api/v1/knowledge/docs/{doc_id}

# 更新文档
PUT /api/v1/knowledge/docs/{doc_id}

# 删除文档
DELETE /api/v1/knowledge/docs/{doc_id}

# 搜索知识库
POST /api/v1/knowledge/search
{
    "query": "缓存穿透解决方案",
    "category": "backend",
    "top_k": 5
}

# 获取分类列表
GET /api/v1/knowledge/categories
```

### 岗位配置接口

```bash
# 创建岗位配置
POST /api/v1/jobs
{
    "company": "字节跳动",
    "position": "后端开发工程师",
    "department": "基础架构",
    "requirements": ["熟悉Go/Java", "熟悉Redis/MySQL"]
}

# 获取岗位列表
GET /api/v1/jobs/list

# 设置默认岗位
POST /api/v1/jobs/{job_id}/set-default
```

### LLM配置接口

```bash
# 获取配置列表
GET /api/v1/llm-configs/list

# 创建配置
POST /api/v1/llm-configs/create

# 测试配置
POST /api/v1/llm-configs/{config_id}/test

# 设置默认配置
POST /api/v1/llm-configs/{config_id}/set-default
```

## 常见问题

### Q1: 端口被占用？

**解决**: 修改 `backend/run.py` 或 `backend/app/core/config.py` 中的端口配置

```python
port=5000  # 改为其他端口如 5001, 8080
```

### Q2: 依赖安装失败？

**解决**: 升级 pip

```bash
python -m pip install --upgrade pip
```

### Q3: 前端无法连接后端？

**解决**: 检查 `frontend/vite.config.ts` 中的代理配置

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:5000',  // 确保与后端端口一致
    changeOrigin: true,
  },
}
```

### Q4: 数据库初始化失败？

**解决**: 检查数据库文件权限，或删除现有数据库文件重新初始化

```bash
# 删除数据库文件
rm backend/interview_agent.db
rm -rf backend/chroma_db
```

### Q5: 向量索引检索不到内容？

**解决**: 检查文档是否正确索引

```bash
# 重新索引现有简历
python backend/index_existing_resumes.py
```

## 开发计划

- [x] 项目初始化
- [x] 后端基础架构
- [x] Agent核心工作流（LangGraph）
- [x] 前端聊天界面
- [x] 简历上传与解析
- [x] 简历向量化索引
- [x] LLM配置界面
- [x] 岗位配置管理
- [x] 知识库管理（Markdown上传、智能分块）
- [ ] 联网搜索功能
- [ ] 面试评估报告
- [ ] 自动总结生成知识库

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## License

MIT License

## 联系方式

- GitHub: https://github.com/FerrymanCsz/PM-agent
- Issues: https://github.com/FerrymanCsz/PM-agent/issues
