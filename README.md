# 通用百科知识图谱问答系统 (General KG-QA)

基于 OwnThink 通用百科知识图谱的 RAG 问答系统，采用混合检索（向量 + BM25 + 图 + HyDE）+ RRF 融合排序。

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS | SPA 界面 |
| 可视化 | D3.js | 知识图谱力导向图 |
| 后端 | FastAPI + uvicorn (4 workers) | API 服务 + 并发 |
| 图数据库 | Neo4j 5 | 知识图谱存储 (6,530 实体 + 6,154 关系) |
| 向量数据库 | Milvus 2.4 | 语义向量检索 (6,530 文档) |
| 关系数据库 | MySQL 8 | 用户认证 |
| Embedding | Ollama bge-m3 (1024维) | 文本向量化 |
| LLM | qwen3.5-plus (阿里 DashScope) | 回答生成 + HyDE + 查询重写 |
| 认证 | bcrypt + JWT | 注册/登录/鉴权 |
| 部署 | Docker Compose | 一键启动 7 个服务 |

## 系统架构

```
用户问题
  │
  ▼
┌─────────────┐
│ 查询重写     │ ← LLM 生成多个查询变体
└──────┬──────┘
       │
  ┌────┼────────────┐
  ▼    ▼            ▼
┌────┐┌────┐┌──────┐┌──────┐
│向量││HyDE││ BM25 ││ 图   │
│检索││检索││关键字 ││检索  │
└──┬─┘└──┬─┘└──┬───┘└──┬───┘
   │     │     │       │
   └──┬──┘     └───┬───┘
      ▼            ▼
   ┌──────────────────┐
   │  RRF 融合排序     │
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ LLM 生成回答      │ ← 基于检索文档 + 知识图谱
   └────────┬─────────┘
            ▼
        回答 + 引用
```

## 项目结构

```
general-kg-qa/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 端点 (auth, qa, knowledge, health)
│   │   ├── data/            # OwnThink 解析器 + Neo4j 导入器
│   │   ├── database/        # Neo4j + MySQL + Milvus 客户端
│   │   ├── eval/            # 评估框架 (metrics + dataset)
│   │   ├── models/          # SQLAlchemy 模型 (User)
│   │   ├── rag/             # RAG 模块
│   │   │   ├── embeddings.py      # bge-m3 embedding 服务
│   │   │   ├── bm25_retriever.py  # BM25 关键字检索 (jieba 分词)
│   │   │   ├── hyde.py            # HyDE 假设性文档检索
│   │   │   ├── query_rewriter.py  # 查询重写 (多变体)
│   │   │   ├── fusion.py          # RRF 融合排序
│   │   │   ├── hybrid_retriever.py # 四路混合检索器
│   │   │   └── doc_generator.py   # 文档生成器
│   │   ├── qa/              # QA 模块
│   │   │   ├── pipeline.py        # QA Pipeline
│   │   │   ├── answer_generator.py # LLM 回答生成
│   │   │   ├── entity_linker.py   # 实体识别
│   │   │   └── subgraph_retriever.py # 子图检索
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Auth 服务
│   │   ├── config.py        # 配置管理
│   │   └── main.py          # FastAPI 入口
│   ├── scripts/
│   │   ├── import_ownthink.py      # 导入 OwnThink 到 Neo4j
│   │   ├── create_relationships.py # 创建实体间关系
│   │   ├── build_index.py          # 构建 Milvus + BM25 索引
│   │   ├── evaluate.py             # RAG 评估脚本
│   │   └── load_test.py            # 并发压测脚本
│   ├── tests/               # 85+ 测试用例
│   ├── Dockerfile
│   └── docker-entrypoint.sh
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios HTTP 客户端
│   │   ├── views/           # Login, Home(问答), Knowledge(图谱)
│   │   ├── components/      # Header 导航
│   │   ├── stores/          # Pinia 认证状态
│   │   └── router/          # 路由守卫
│   ├── Dockerfile
│   └── nginx.conf           # Nginx 反向代理
├── docker-compose.yml       # 一键部署 7 个服务
├── .env.example             # 环境变量模板
└── pyproject.toml           # Python 依赖
```

## 快速开始

### 方式一：Docker Compose 一键部署（推荐）

```bash
git clone git@github.com:zhipingdeng/general-kg-qa.git
cd general-kg-qa

# 配置 LLM API Key
cp .env.example .env
# 编辑 .env 设置 LLM_API_KEY

# 一键启动（自动构建镜像 + 导入数据 + 构建索引）
docker-compose up -d
```

启动后访问：
- 前端: http://localhost:80
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- Neo4j: http://localhost:7474 (neo4j/your_password)

### 方式二：本地开发

```bash
# 1. 启动数据库
docker-compose up -d neo4j mysql etcd minio milvus-standalone

# 2. 后端
conda create -n general-kg-qa python=3.11 -y
conda activate general-kg-qa
pip install -e ".[dev]"

# 导入数据（首次）
python backend/scripts/import_ownthink.py
python backend/scripts/create_relationships.py
python backend/scripts/build_index.py

# 启动
cd backend && python run.py

# 3. 前端
cd frontend
npm install --registry https://registry.npmjs.org
npm run dev
```

## API 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/auth/register | 注册 | ✗ |
| POST | /api/v1/auth/login | 登录 | ✗ |
| GET | /api/v1/auth/me | 当前用户 | ✓ |
| POST | /api/v1/qa | 知识问答（混合检索） | ✓ |
| GET | /api/v1/knowledge/graph | 知识图谱数据 | ✓ |
| GET | /api/v1/health | 健康检查 | ✗ |

## 混合检索流程

1. **查询重写** — LLM 将原始问题改写为多个变体，扩大检索覆盖
2. **HyDE** — LLM 生成假设性回答文档，用于语义检索
3. **向量检索** — 用原始问题 + HyDE 文档的 embedding 在 Milvus 中搜索
4. **BM25 检索** — jieba 分词后的关键字检索
5. **图检索** — 实体识别 → Neo4j 子图查询（属性 + 关系）
6. **RRF 融合** — Reciprocal Rank Fusion 合并所有检索结果
7. **LLM 生成** — 基于融合后的文档 + 图谱信息生成最终回答

## 评估框架

```bash
# 运行评估（50 个 KgCLUE 样本）
cd backend && python scripts/evaluate.py
```

评估指标：

| 类别 | 指标 | 说明 |
|------|------|------|
| 检索 | Recall@5 | 正确文档被检索到的比例 |
| 检索 | Precision@5 | 检索结果中正确文档的比例 |
| 检索 | MRR | 第一个正确结果的排名倒数 |
| 检索 | Hit Rate | 至少有一个正确结果的比例 |
| 检索 | NDCG@5 | 归一化折损累积增益 |
| 生成 | Exact Match | 答案完全匹配 |
| 生成 | F1 Score | token 级别的 F1 |
| 生成 | Contains Answer | 参考答案是否被包含 |
| 性能 | avg/p50/p95 | 响应延迟 (ms) |

## 知识图谱

数据来源: [OwnThink 通用百科知识图谱](https://github.com/ownthink/KnowledgeGraphData)

- 实体节点: 6,530 个
- TAG 关系: 6,148 条 (实体 → 标签分类)
- 地理关系: 6 条 (所属地区)
- Milvus 文档: 6,530 条 (向量索引)
- 数据采样: 100,000 条三元组

## Docker 服务

| 服务 | 端口 | 用途 |
|------|------|------|
| frontend-kgqa | 80 | Nginx + Vue 3 |
| backend-kgqa | 8000 | FastAPI (4 workers) |
| neo4j-kgqa | 7687/7474 | 知识图谱 |
| mysql-kgqa | 3307 | 用户认证 |
| milvus-kgqa | 19530 | 向量检索 |
| etcd-kgqa | 内部 | Milvus 元数据 |
| minio-kgqa | 内部 | Milvus 对象存储 |

## 评估结果

基于 KgCLUE 测试集（12 个匹配 OwnThink 实体的样本）：

### 检索质量

| 指标 | 分值 | 说明 |
|------|------|------|
| Recall@5 | **1.0000** | 所有正确实体均被检索到 |
| Precision@5 | **0.9583** | 检索结果准确率 95.83% |
| MRR | **1.0000** | 第一个正确结果始终排第一 |
| Hit Rate | **1.0000** | 100% 命中 |
| NDCG@5 | **1.0000** | 排序质量完美 |

### 生成质量

| 指标 | 分值 | 说明 |
|------|------|------|
| Contains Answer | **58.33%** | 参考答案被包含在生成答案中 |
| F1 Score | **31.31%** | token 级别重叠度 |
| Exact Match | 0.00% | LLM 生成自然语言，格式不同属预期 |

### 响应延迟

| 指标 | 耗时 |
|------|------|
| avg | 21.2s |
| p50 | 21.5s |
| p95 | 30.8s |

延迟主要来自 LLM API 调用（HyDE + 查询重写 + 回答生成，共 3-4 次）。

## 测试

```bash
cd backend && pytest tests/ -v
# 85+ passed
```

## License

MIT
