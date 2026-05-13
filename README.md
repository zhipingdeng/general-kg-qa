# 通用百科知识图谱问答系统 (General KG-QA)

基于 OwnThink 通用百科知识图谱的智能问答系统，支持自然语言提问、知识图谱可视化。

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS | SPA 界面 |
| 可视化 | D3.js | 知识图谱力导向图 |
| 后端 | FastAPI + gunicorn(uvicorn workers) | API 服务 + 并发 |
| 图数据库 | Neo4j 5 | 知识图谱存储 (6530 实体 + 6148 条关系) |
| 关系数据库 | MySQL 8 | 用户认证数据 |
| LLM | qwen3.5-plus (阿里 DashScope) | 自然语言回答生成 |
| 认证 | bcrypt + JWT | 注册/登录/鉴权 |

## 项目结构

```
general-kg-qa/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 端点 (auth, qa, knowledge, health)
│   │   ├── data/            # OwnThink 解析器 + Neo4j 导入器
│   │   ├── database/        # Neo4j + MySQL 客户端
│   │   ├── models/          # SQLAlchemy 模型 (User)
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Auth 服务 (bcrypt + JWT)
│   │   ├── qa/              # QA Pipeline (实体识别→子图检索→LLM生成)
│   │   ├── config.py        # 配置管理
│   │   └── main.py          # FastAPI 入口
│   ├── scripts/             # 数据导入脚本
│   ├── gunicorn_conf.py     # gunicorn 多 worker 配置
│   ├── run.py               # 启动入口
│   └── tests/               # 44 个测试用例
├── frontend/
│   └── src/
│       ├── api/             # Axios HTTP 客户端
│       ├── views/           # Login, Home(问答), Knowledge(图谱)
│       ├── components/      # Header 导航
│       ├── stores/          # Pinia 认证状态
│       └── router/          # 路由守卫
├── docker-compose.yml       # Neo4j + MySQL 容器
├── .env.example             # 环境变量模板
└── pyproject.toml           # Python 依赖
```

## 快速开始

### 1. 克隆项目

```bash
git clone git@github.com:zhipingdeng/general-kg-qa.git
cd general-kg-qa
```

### 2. 启动数据库

```bash
docker-compose up -d
# Neo4j: http://localhost:7474 (neo4j/kgqa123)
# MySQL: localhost:3307 (kgqa/kgqa123)
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 设置 LLM_API_KEY 等
```

### 4. 后端

```bash
conda create -n general-kg-qa python=3.11 -y
conda activate general-kg-qa
pip install -e ".[dev]"

# 导入知识图谱数据 (首次)
python backend/scripts/import_ownthink.py

# 创建实体关系 (首次)
python backend/scripts/create_relationships.py

# 启动 (开发模式)
cd backend && python run.py

# 启动 (生产模式, gunicorn 多 worker)
cd backend && python run.py --prod
```

后端运行在 http://localhost:8000，API 文档: http://localhost:8000/docs

### 5. 前端

```bash
cd frontend
npm install --registry https://registry.npmjs.org
npm run dev
```

前端运行在 http://localhost:5173

## API 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/auth/register | 注册 | ✗ |
| POST | /api/v1/auth/login | 登录 | ✗ |
| GET | /api/v1/auth/me | 当前用户 | ✓ |
| POST | /api/v1/qa | 知识问答 | ✓ |
| GET | /api/v1/knowledge/graph | 知识图谱数据 | ✓ |
| GET | /api/v1/health | 健康检查 | ✗ |

## 知识图谱

数据来源: [OwnThink 通用百科知识图谱](https://github.com/ownthink/KnowledgeGraphData)

- 实体节点: 6,530 个
- TAG 关系: 6,148 条 (实体 → 标签分类)
- 地理关系: 6 条 (所属地区)
- 数据采样: 100,000 条三元组

## 测试

```bash
cd backend && pytest tests/ -v
# 44 passed
```

## 并发架构

```
                gunicorn master
        ┌───────┬───────┬───────┐
   uvicorn  uvicorn  uvicorn  uvicorn
   worker1  worker2  worker3  workerN
        └───────┴───────┴───────┘
          │           │
       Neo4j       MySQL
     (连接池)     (连接池)
```

- 开发: `python run.py` (单 uvicorn + reload)
- 生产: `python run.py --prod` (gunicorn, workers = CPU*2+1)

## License

MIT
