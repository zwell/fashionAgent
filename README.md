# FashionAgent 🧵

> Fashion e-commerce multi-agent system powered by LangGraph

一个基于 LangGraph 的时尚电商多智能体协作系统。Master Agent 编排调度 5 大子 Agent（设计/视觉/营销/数据/供应链），实现"自动上新"、"智能补货"、"清仓决策"等电商核心业务场景的端到端自动化。

## Features

- **LangGraph StateGraph 编排**：Master Agent 状态机驱动的多 Agent 任务分发
- **MCP 技能注册中心**：L1 原子技能 + L2 组合技能，语义化封装 + 自然语言搜索
- **三层混合记忆**：Redis（短期）+ Milvus（中期向量）+ Neo4j（长期图谱）
- **全链路追踪**：LangSmith 集成，每步 CoT 可监控
- **FastAPI 异步网关**：高并发任务处理 + WebSocket 实时推送
- **真实数据支撑**：基于 H&M 数据集 schema（105K SKU, 31M 交易），内置种子数据开箱即用

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Start API server
uvicorn fashion_agent.gateway.app:app --reload

# Start with Docker (Redis)
docker-compose up -d
uvicorn fashion_agent.gateway.app:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/tasks` | POST | Submit generic task |
| `/api/v1/tasks/copywriting` | POST | Generate product copy |
| `/api/v1/tasks/restock` | POST | Get restock recommendation |
| `/api/v1/tasks/clearance` | POST | Get clearance decision |
| `/api/v1/tasks/trend` | POST | Trend analysis |
| `/api/v1/tasks/launch` | POST | New product launch workflow |
| `/api/v1/skills` | GET | List registered skills |
| `/api/v1/skills/search` | GET | Search skills by keyword |

## Architecture

```
FastAPI Gateway
    └── Master Agent (LangGraph StateGraph)
            ├── Marketing Agent (ToT: copy variants)
            ├── Data Agent (CoT: step-by-step analysis)
            ├── SupplyChain Agent (ReAct: observe → act)
            ├── Design Agent (Phase 2)
            └── Visual Agent (Phase 2)
                    │
            MCP Skills Registry
            ├── L1: 查询库存 / 销量预测 / 竞品分析 / 趋势分析 / 文案生成
            └── L2: 智能补货 / 清仓决策 / 新品上架
                    │
            Memory Manager
            ├── Redis (short-term sessions)
            ├── Milvus (mid-term vectors) [Phase 3]
            └── Neo4j (long-term graph) [Phase 3]
```

## Dataset

Built on the [H&M Personalized Fashion Recommendations](https://www.kaggle.com/c/h-and-m-personalized-fashion-recommendations) dataset schema:

- **105,542** product SKUs with 25 attributes
- **31,788,324** purchase transactions
- **1,371,980** customer profiles
- **105,000+** product images

The project ships with seed data (20 articles, 30 transactions, 15 customers, 6 suppliers) for zero-setup development. See `docs/DATA_STRATEGY.md` for full dataset import instructions.

## Project Structure

```
src/fashion_agent/
├── core/           # Config, models, data loader, logging, exceptions
├── gateway/        # FastAPI app, routes, middleware
├── orchestrator/   # LangGraph Master Agent, state, workflows
├── agents/         # Sub-agents (Marketing, SupplyChain, Data, ...)
├── skills/         # MCP skill registry, L1 atomic & L2 composite skills
├── memory/         # Short-term (Redis), mid-term (Milvus), long-term (Neo4j)
└── tracing/        # LangSmith integration
```

## Docs

- [Project Plan](docs/PROJECT_PLAN.md) — full architecture & implementation roadmap
- [Data Strategy](docs/DATA_STRATEGY.md) — dataset selection & import guide
