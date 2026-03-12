# 面试模拟Agent系统 - 安装指南

## 方案对比

### 方案1: 本地Python（推荐初学者）
**难度**: ⭐ 简单
**适用**: 个人开发、快速测试

**优点:**
- 安装简单，直接使用系统Python
- 启动快速，资源占用少
- 不需要额外工具

**缺点:**
- 依赖可能和系统其他项目冲突
- 不方便管理多个项目

---

### 方案2: Conda（推荐数据科学）
**难度**: ⭐⭐ 中等
**适用**: 数据科学、AI项目、多项目管理

**优点:**
- 环境完全隔离
- 依赖管理强大，自动解决冲突
- 支持科学计算库
- 跨平台一致

**缺点:**
- 需要安装Miniconda/Anaconda
- 包不如pip丰富

---

### 方案3: Docker（推荐团队/生产）
**难度**: ⭐⭐⭐ 较复杂
**适用**: 团队协作、生产部署、环境一致性要求高

**优点:**
- 完全隔离，环境一致
- 可移植性强
- 适合CI/CD

**缺点:**
- 需要学习Docker
- 资源占用较多
- 启动稍慢

---

## 🎯 推荐方案：Conda

**为什么推荐Conda？**
1. 本项目使用LangChain/AI库，Conda管理更好
2. 环境隔离，不影响其他项目
3. 依赖冲突解决能力强
4. 适合长期维护

---

## 🚀 安装步骤（Conda方案）

### 第一步：安装Miniconda

1. 下载Miniconda（Windows）:
   ```
   https://docs.conda.io/en/latest/miniconda.html
   ```

2. 运行安装程序，按默认选项安装

3. 安装完成后，打开 **Anaconda Prompt** 或重启终端

### 第二步：创建环境

```bash
# 创建Python 3.11环境
conda create -n interview_agent python=3.11 -y

# 激活环境
conda activate interview_agent
```

### 第三步：安装依赖

```bash
# 进入后端目录
cd d:\trae\PM_agent\backend

# 安装依赖
pip install -r requirements.txt
```

### 第四步：启动服务

```bash
# 启动后端
python run.py
```

看到以下输出表示成功：
```
🚀 启动 面试模拟Agent系统 v1.0.0
✅ 数据库初始化完成
INFO:     Uvicorn running on http://0.0.0.0:5000
```

### 第五步：验证

打开浏览器访问：
- 前端: http://localhost:3000/
- 后端API: http://localhost:5000/docs

---

## 📋 备选方案：本地Python

如果不需要环境隔离，可以直接使用本地Python：

```bash
# 进入后端目录
cd d:\trae\PM_agent\backend

# 创建虚拟环境（可选但推荐）
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动
python run.py
```

---

## 🔧 常见问题

### Q1: pip安装速度慢？
**解决**: 使用清华镜像
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: 端口被占用？
**解决**: 修改 `run.py` 中的端口
```python
port=5000  # 改为其他端口如 5001, 8080
```

### Q3: 依赖安装失败？
**解决**: 升级pip
```bash
python -m pip install --upgrade pip
```

### Q4: 如何退出环境？
```bash
conda deactivate  # Conda环境
# 或
deactivate  # venv环境
```

---

## 📁 项目结构

```
PM_agent/
├── backend/          # 后端代码
│   ├── app/         # 应用代码
│   ├── requirements.txt
│   └── run.py       # 启动脚本
├── frontend/        # 前端代码
│   ├── src/
│   └── package.json
└── docs/           # 文档
```

---

## ✅ 安装检查清单

- [ ] Miniconda已安装
- [ ] 环境 `interview_agent` 已创建
- [ ] 依赖安装完成（无报错）
- [ ] 后端服务启动成功
- [ ] 前端页面可以访问
- [ ] API文档可以访问

---

## 🆘 需要帮助？

如果遇到问题：
1. 检查Python版本: `python --version` (需要3.11+)
2. 检查pip: `pip --version`
3. 查看错误日志
4. 确认端口未被占用

---

**安装完成后，访问 http://localhost:3000/ 开始使用！**
