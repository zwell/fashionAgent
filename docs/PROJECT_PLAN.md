# FashionAgent - 时尚电商多智能体系统 项目规划

## 一、项目概述

FashionAgent 是一个基于 LangGraph 的时尚电商多智能体协作系统。系统以 Master Agent 为核心编排引擎，协调设计、视觉、营销、数据分析、供应链等多个专业子 Agent，实现"自动上新"、"智能补货"、"清仓决策"等电商核心业务场景的端到端自动化。

### 核心亮点

- **LangGraph 状态机编排**：复杂的多 Agent 生命周期管理与任务分发
- **MCP 技能注册中心**：可插拔的 L1 原子技能 + L2 组合技能体系
- **三层混合记忆架构**：Redis（短期）+ Milvus（中期）+ Neo4j（长期）
- **全链路可追溯**：LangSmith 集成，每步 CoT 可监控、可回滚
- **高并发异步网关**：FastAPI + Asyncio 任务处理引擎

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Gateway                          │
│                   (Async Task Router + WebSocket)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Master Agent (LangGraph)                     │  │
│  │         State Machine + Task Orchestrator                 │  │
│  │                                                           │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ ┌─────┐  │  │
│  │  │ Design  │ │ Visual  │ │Marketing│ │ Data  │ │Supply│  │  │
│  │  │ Agent   │ │ Agent   │ │ Agent   │ │ Agent │ │Chain │  │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └───┬───┘ └──┬──┘  │  │
│  └───────┼──────────┼──────────┼──────────┼────────┼────────┘  │
│          │          │          │          │        │            │
│  ┌───────┴──────────┴──────────┴──────────┴────────┴────────┐  │
│  │              MCP Skills Registry                          │  │
│  │  ┌──────────────────┐  ┌────────────────────────────┐     │  │
│  │  │ L1 Atomic Skills │  │   L2 Composite Skills      │     │  │
│  │  │ • ERP Query      │  │   • Restock Workflow       │     │  │
│  │  │ • Logistics Track│  │   • Clearance Workflow     │     │  │
│  │  │ • Competitor Scan│  │   • New Product Launch     │     │  │
│  │  │ • Image Generate │  │   • Daily Reflection       │     │  │
│  │  └──────────────────┘  └────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            Multi-Dimensional Memory                       │  │
│  │  ┌─────────┐    ┌──────────┐    ┌──────────────┐         │  │
│  │  │  Redis  │    │  Milvus  │    │    Neo4j     │         │  │
│  │  │ 短期会话 │    │ 中期画像  │    │  长期知识图谱 │         │  │
│  │  └─────────┘    └──────────┘    └──────────────┘         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         Observability (LangSmith + Custom Tracer)         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、模块详细设计

### 模块 1：多智能体编排中枢 (Orchestration Layer)

**目标**：基于 LangGraph 构建 Master Agent，管理子 Agent 生命周期。

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| Master Agent | LangGraph StateGraph | 中央编排器，状态机驱动 |
| 子 Agent 通信 | LangGraph Channel | Agent 间消息传递 |
| 状态管理 | TypedDict + Pydantic | 类型安全的状态定义 |
| 人工审核节点 | LangGraph Interrupt | 支持 human-in-the-loop |

**5 大子 Agent 设计**：

1. **Design Agent（设计引擎）**
   - 能力：根据趋势数据和市场分析生成产品设计方案
   - 推理范式：CoT（逐步推理设计灵感 → 元素组合 → 方案输出）
   - 技能调用：竞品分析、趋势预测、设计模板生成

2. **Visual Agent（视觉生产）**
   - 能力：生成商品图、模特图、场景图
   - 推理范式：ReAct（观察设计稿 → 判断风格 → 调用生成工具 → 评估结果）
   - 技能调用：图像生成、图像编辑、风格迁移

3. **Marketing Agent（营销大脑）**
   - 能力：撰写商品文案、标题优化、推广策略
   - 推理范式：ToT（多路径探索不同文案风格 → 评估 → 选择最优）
   - 技能调用：文案生成、SEO 分析、A/B 测试建议

4. **Data Agent（数据分析）**
   - 能力：销量预测、用户画像分析、市场趋势
   - 推理范式：CoT（数据收集 → 特征分析 → 洞察生成）
   - 技能调用：数据库查询、统计分析、可视化生成

5. **SupplyChain Agent（供应链）**
   - 能力：库存管理、补货建议、物流追踪
   - 推理范式：ReAct（查询库存 → 分析需求 → 执行补货/清仓）
   - 技能调用：ERP 查询、物流追踪、补货计算

**核心场景 - 自动上新 SOP**：

```
[用户指令: "春季新品上新"]
        │
        ▼
  Master Agent (解析意图, 创建任务)
        │
        ▼
  Design Agent (生成设计草图)
        │
        ├──────────────┐
        ▼              ▼
  Visual Agent    Marketing Agent
  (模特图生成)     (文案撰写)
        │              │
        └──────┬───────┘
               ▼
       Human Review Node
        (人工/自动评审)
               │
        ┌──────┴──────┐
        │ approved    │ rejected
        ▼             ▼
  Push to Platform  Feedback Loop
```

---

### 模块 2：MCP Skills 技能化体系

**目标**：基于 MCP 协议构建可插拔的技能注册中心。

#### L1 原子技能 (Atomic Skills)

| 技能名称 | 语义描述 | 输入 | 输出 |
|---------|---------|------|------|
| `erp_inventory_query` | 查询指定 SKU 的当前库存量 | SKU ID | 库存数据 |
| `logistics_tracking` | 追踪物流订单状态 | 订单号 | 物流状态 |
| `competitor_analysis` | 分析竞品价格和销量 | 品类/关键词 | 竞品报告 |
| `image_generation` | 生成商品/模特图片 | 设计描述 | 图片 URL |
| `copywriting` | 生成商品文案 | 产品信息 | 文案文本 |
| `sales_forecast` | 预测 SKU 未来销量 | SKU + 历史数据 | 预测值 |
| `trend_analysis` | 时尚趋势分析 | 品类/季节 | 趋势报告 |

#### L2 组合技能 (Composite Skills)

| 技能名称 | 组合的 L1 技能 | 说明 |
|---------|--------------|------|
| `restock_workflow` | inventory_query + sales_forecast + logistics | 智能补货流程 |
| `clearance_workflow` | inventory_query + competitor_analysis + copywriting | 清仓决策流程 |
| `new_product_launch` | trend_analysis + image_generation + copywriting | 新品上架流程 |

#### 语义化封装

```python
@skill(
    name="查询库存",
    description="查询指定商品的当前库存数量、仓库分布、和可用状态",
    tags=["库存", "ERP", "供应链"],
    examples=["帮我查一下SKU12345的库存", "A仓还有多少件红色连衣裙"]
)
async def erp_inventory_query(sku_id: str) -> InventoryResult:
    ...
```

Agent 通过自然语言搜索技能：`"查询库存" + "销量预测" = "补货建议"`

---

### 模块 3：多维记忆网络 (Multi-Dimensional Memory)

#### 三层架构

| 层级 | 存储 | 数据类型 | TTL | 用途 |
|------|------|---------|-----|------|
| L1 短期 | Redis | 会话上下文、临时变量 | 24h | 当前任务的工作记忆 |
| L2 中期 | Milvus | SKU 向量画像、用户偏好 | 90d | 语义检索与相似性匹配 |
| L3 长期 | Neo4j | 实体关系图谱 | 永久 | SKU 生命周期、供应链关系 |

#### Entity Memory - SKU 全生命周期

```
(SKU_12345) ──[设计灵感]──> (Trend_SS2026)
     │
     ├──[版型参数]──> (Pattern_A01)
     ├──[退货原因]──> (Issue: 色差)
     ├──[市场反馈]──> (Rating: 4.2/5)
     ├──[供应商]──> (Supplier_CN_003)
     └──[关联推荐]──> (SKU_12346, SKU_12400)
```

#### Reflection Mechanism - 每日反思

```python
class DailyReflection:
    """
    每日夜间批处理：
    1. 汇总当日所有 Agent 决策
    2. 分析成功/失败案例（如：为何某款滞销）
    3. 提取经验教训写入长期记忆
    4. 更新 Agent 策略权重
    """
    async def reflect(self, date: str):
        decisions = await self.get_daily_decisions(date)
        analysis = await self.analyze_outcomes(decisions)
        insights = await self.extract_insights(analysis)
        await self.write_to_long_term_memory(insights)
```

---

### 模块 4：技术基础设施

#### 4.1 异步任务网关 (FastAPI + Asyncio)

```python
# 高并发任务处理
app = FastAPI()

@app.post("/tasks/submit")
async def submit_task(task: TaskRequest):
    task_id = await task_queue.enqueue(task)
    return {"task_id": task_id, "status": "queued"}

@app.websocket("/tasks/{task_id}/stream")
async def stream_progress(websocket: WebSocket, task_id: str):
    async for event in task_monitor.subscribe(task_id):
        await websocket.send_json(event)
```

#### 4.2 可追溯性体系 (LangSmith Integration)

- 每个 Agent 的 CoT 自动上报到 LangSmith
- 支持按 task_id 回溯完整执行链路
- 异常决策自动标记 + 告警
- 支持 A/B 对比不同 Agent 策略的效果

#### 4.3 评估体系 (Ragas)

- 单元测试：每个 Skill 的输入输出验证
- 端到端评估：完整 SOP 流程的质量评分
- 指标：Faithfulness, Answer Relevancy, Context Precision

---

## 四、项目目录结构

```
fashionAgent/
├── README.md
├── pyproject.toml                    # 项目依赖管理 (Poetry/uv)
├── docker-compose.yml                # Redis + Milvus + Neo4j + API
├── .env.example                      # 环境变量模板
│
├── src/
│   └── fashion_agent/
│       ├── __init__.py
│       │
│       ├── core/                     # 核心基础设施
│       │   ├── config.py             # 配置管理
│       │   ├── logging.py            # 日志 + LangSmith tracer
│       │   └── exceptions.py         # 自定义异常
│       │
│       ├── gateway/                  # FastAPI 网关层
│       │   ├── app.py                # FastAPI 应用入口
│       │   ├── routes/
│       │   │   ├── tasks.py          # 任务提交/查询 API
│       │   │   ├── agents.py         # Agent 状态查询 API
│       │   │   └── skills.py         # Skills 注册/查询 API
│       │   ├── middleware/
│       │   │   ├── tracing.py        # 链路追踪中间件
│       │   │   └── rate_limit.py     # 限流中间件
│       │   └── websocket.py          # WebSocket 实时推送
│       │
│       ├── orchestrator/             # 编排中枢
│       │   ├── master_agent.py       # Master Agent (LangGraph StateGraph)
│       │   ├── state.py              # 全局状态定义
│       │   ├── router.py             # 任务路由逻辑
│       │   └── workflows/
│       │       ├── new_product.py    # 自动上新 SOP
│       │       ├── restock.py        # 智能补货流程
│       │       └── clearance.py      # 清仓决策流程
│       │
│       ├── agents/                   # 子 Agent 实现
│       │   ├── base.py               # Agent 基类
│       │   ├── design_agent.py       # 设计引擎 Agent
│       │   ├── visual_agent.py       # 视觉生产 Agent
│       │   ├── marketing_agent.py    # 营销大脑 Agent
│       │   ├── data_agent.py         # 数据分析 Agent
│       │   └── supply_chain_agent.py # 供应链 Agent
│       │
│       ├── skills/                   # MCP 技能体系
│       │   ├── registry.py           # Skills 注册中心
│       │   ├── base.py               # Skill 基类 + 装饰器
│       │   ├── search.py             # 语义化技能搜索
│       │   ├── l1_atomic/            # L1 原子技能
│       │   │   ├── erp_inventory.py
│       │   │   ├── logistics.py
│       │   │   ├── competitor.py
│       │   │   ├── image_gen.py
│       │   │   ├── copywriting.py
│       │   │   ├── sales_forecast.py
│       │   │   └── trend_analysis.py
│       │   └── l2_composite/         # L2 组合技能
│       │       ├── restock.py
│       │       ├── clearance.py
│       │       └── product_launch.py
│       │
│       ├── memory/                   # 多维记忆网络
│       │   ├── manager.py            # 记忆管理器（统一接口）
│       │   ├── short_term.py         # Redis 短期记忆
│       │   ├── mid_term.py           # Milvus 向量记忆
│       │   ├── long_term.py          # Neo4j 图谱记忆
│       │   ├── entity.py             # Entity Memory (SKU 画像)
│       │   └── reflection.py         # 每日反思机制
│       │
│       └── tracing/                  # 可追溯性
│           ├── langsmith.py          # LangSmith 集成
│           ├── tracer.py             # 自定义 Tracer
│           └── callbacks.py          # LangChain Callbacks
│
├── tests/
│   ├── conftest.py
│   ├── unit/                         # 单元测试
│   │   ├── test_skills/
│   │   ├── test_memory/
│   │   └── test_agents/
│   ├── integration/                  # 集成测试
│   │   ├── test_workflows.py
│   │   └── test_orchestrator.py
│   └── evaluation/                   # Ragas 评估
│       ├── test_e2e_quality.py
│       └── datasets/
│
├── scripts/
│   ├── seed_neo4j.py                # 初始化 Neo4j 图谱数据
│   ├── seed_milvus.py               # 初始化 Milvus 向量数据
│   └── run_reflection.py            # 手动触发每日反思
│
└── docs/
    ├── PROJECT_PLAN.md               # 本文档
    ├── API.md                        # API 文档
    └── ARCHITECTURE.md               # 架构详解
```

---

## 五、技术栈清单

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **语言** | Python | 3.11+ | 主语言 |
| **Web 框架** | FastAPI | 0.115+ | 异步网关 |
| **Agent 框架** | LangGraph | 0.3+ | 多 Agent 编排 |
| **LLM 框架** | LangChain | 0.3+ | LLM 调用 + 工具链 |
| **短期存储** | Redis | 7+ | 会话缓存 |
| **向量数据库** | Milvus | 2.4+ | 语义检索 |
| **图数据库** | Neo4j | 5+ | 知识图谱 |
| **可观测性** | LangSmith | latest | 链路追踪 |
| **评估** | Ragas | 0.2+ | 质量评估 |
| **容器化** | Docker Compose | 2.x | 本地开发环境 |
| **依赖管理** | uv / Poetry | latest | Python 包管理 |
| **测试** | pytest + pytest-asyncio | latest | 测试框架 |
| **类型检查** | Pydantic v2 | 2.x | 数据验证 |

---

## 六、实施路线

### Phase 1 - 基础骨架 🏗️

**范围**：搭建项目结构、核心基础设施、单个 Agent 可运行

- [ ] 项目初始化：pyproject.toml, docker-compose.yml, 基础配置
- [ ] FastAPI 网关：基础路由 + 健康检查 + WebSocket 框架
- [ ] LangGraph Master Agent：最简状态机，支持单任务分发
- [ ] 第一个子 Agent（Marketing Agent）：文案生成能力
- [ ] MCP Skills 基础框架：Skill 基类 + 注册中心 + 1-2 个 L1 技能
- [ ] Redis 短期记忆：会话上下文存储
- [ ] LangSmith 基础集成：Tracer 接入

**交付物**：能通过 API 提交任务，Master Agent 调度 Marketing Agent 生成一段商品文案

---

### Phase 2 - 多 Agent 协作 🤝

**范围**：实现多 Agent 并行协作 + 完整上新 SOP

- [ ] 补全 5 个子 Agent（Design, Visual, Data, SupplyChain）
- [ ] LangGraph 并行执行：Visual + Marketing Agent 并行
- [ ] Human-in-the-loop：评审节点（LangGraph Interrupt）
- [ ] 完整"自动上新"SOP 工作流
- [ ] L1 原子技能全部实现（模拟数据）
- [ ] 推理范式实现：CoT / ReAct / ToT 分别用于不同 Agent

**交付物**：完整的自动上新流程，从指令到生成设计 + 图片 + 文案 + 审核

---

### Phase 3 - 记忆 + 技能体系 🧠

**范围**：完善记忆网络 + MCP 技能体系

- [ ] Milvus 中期记忆：SKU 向量画像存储与检索
- [ ] Neo4j 长期图谱：Entity Memory（SKU 关系网络）
- [ ] Memory Manager 统一接口
- [ ] 每日反思机制（Reflection Mechanism）
- [ ] L2 组合技能：补货 / 清仓 / 新品上架
- [ ] 语义化技能搜索：自然语言 → 技能匹配
- [ ] 补货 + 清仓工作流实现

**交付物**：Agent 具备记忆能力，能基于历史数据做更智能的决策

---

### Phase 4 - 生产化 + 评估 🚀

**范围**：生产级质量保证 + 评估体系

- [ ] Ragas 评估集成：Faithfulness, Relevancy, Precision
- [ ] 单元测试覆盖：所有 Skills + Memory 模块
- [ ] 集成测试：完整工作流端到端
- [ ] 性能优化：并发控制、连接池、缓存策略
- [ ] 错误处理 + 重试机制 + 降级策略
- [ ] API 文档完善（OpenAPI + 自定义文档）
- [ ] 部署文档 + CI/CD 配置

**交付物**：生产就绪的系统，有完善的测试和评估体系

---

## 七、关键设计决策

### 1. 为什么选 LangGraph 而不是 AutoGen / CrewAI？

- **精细控制**：LangGraph 的 StateGraph 提供了显式的状态机控制，适合复杂业务流程
- **持久化**：内置 checkpointing，支持长时间运行的工作流
- **Human-in-the-loop**：原生 Interrupt 机制，完美适配人工审核需求
- **可观测性**：与 LangSmith 深度集成

### 2. 三层记忆架构的考量

- **Redis**：高性能、低延迟，适合热数据（当前会话、任务状态）
- **Milvus**：专业向量检索，适合语义相似性匹配（找相似 SKU、相似用户）
- **Neo4j**：图结构天然适合表达实体关系（SKU ↔ 供应商 ↔ 品类 ↔ 趋势）

### 3. MCP 协议的选择

- **标准化**：MCP 是 Anthropic 推出的开放标准，社区活跃
- **可插拔**：每个 Skill 独立注册，支持热插拔
- **自描述**：语义化封装让 Agent 能自动发现和组合工具

---

## 八、模拟数据策略

由于项目是演示性质，以下数据将使用模拟实现：

| 数据源 | 模拟方式 |
|--------|---------|
| ERP 库存 | JSON 文件 + 内存数据库 |
| 物流信息 | Faker 生成模拟物流轨迹 |
| 竞品数据 | 预设 JSON 数据集 |
| 图片生成 | 调用免费 API 或返回占位图 |
| 销售数据 | 随机生成 + 预设趋势曲线 |
| 用户评价 | 预设评价数据集 |

---

## 九、环境变量

```env
# LLM
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o

# Redis
REDIS_URL=redis://localhost:6379/0

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LangSmith
LANGSMITH_API_KEY=ls-xxx
LANGSMITH_PROJECT=fashion-agent
LANGSMITH_TRACING=true

# App
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

---

## 十、如何运行

```bash
# 1. 克隆项目
git clone <repo-url> && cd fashionAgent

# 2. 安装依赖
uv sync  # 或 poetry install

# 3. 启动基础设施
docker-compose up -d  # Redis + Milvus + Neo4j

# 4. 初始化数据
python scripts/seed_neo4j.py
python scripts/seed_milvus.py

# 5. 启动服务
uvicorn src.fashion_agent.gateway.app:app --reload

# 6. 运行测试
pytest tests/ -v
```
