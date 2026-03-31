# FashionAgent API 接口文档

## 基础信息

| 项目 | 值 |
|------|---|
| Base URL | `http://localhost:8000` |
| 协议 | HTTP/1.1 |
| 内容类型 | `application/json` |
| 交互式文档 | Swagger UI → `/docs`，ReDoc → `/redoc` |
| OpenAPI 规范 | `/openapi.json` |
| 控制台 | `http://localhost:8000/` (交互式前端) |

---

## 1. 健康检查

### `GET /health`

检查系统运行状态。

**Response**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "skills_registered": 8
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 系统状态 |
| version | string | 系统版本 |
| skills_registered | int | 已注册技能数量 |

---

## 2. 任务 API (Task Endpoints)

所有任务 API 通过 Master Agent 编排，自动路由到对应子 Agent 执行。

### 2.1 提交通用任务

### `POST /api/v1/tasks`

灵活提交任意类型的任务。

**Request Body**

```json
{
  "task_type": "copywriting",
  "instruction": "给红色连衣裙写促销文案",
  "params": {
    "article_id": "0126589003",
    "preferred_style": "promotion"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_type | string | ✅ | 任务类型枚举值 |
| instruction | string | ✅ | 自然语言指令 |
| params | object | ❌ | 额外参数（传递给子 Agent） |

**task_type 枚举**

| 值 | 说明 | 路由的 Agent(s) |
|---|------|----------------|
| `copywriting` | 文案生成 | Marketing Agent |
| `restock` | 智能补货 | SupplyChain Agent |
| `clearance` | 清仓决策 | SupplyChain + Marketing Agent |
| `trend_analysis` | 趋势分析 | Data Agent |
| `new_product_launch` | 新品上架 | Data + Marketing Agent |
| `inventory_check` | 库存查询 | SupplyChain Agent |
| `general` | 通用任务 | Data Agent |

**Response**

```json
{
  "task_id": "a1b2c3d4",
  "status": "completed",
  "agents_involved": ["marketing_agent"],
  "all_success": true,
  "results": [
    {
      "success": true,
      "agent": "marketing_agent",
      "article_id": "0126589003",
      "selected_copy": "...",
      "selected_style": "promotion",
      "all_variants": {
        "product_description": "...",
        "promotion": "...",
        "social_media": "..."
      },
      "reasoning": "Generated 3 copy variants using ToT approach..."
    }
  ]
}
```

---

### 2.2 文案生成

### `POST /api/v1/tasks/copywriting`

Marketing Agent 为商品生成多风格文案。

**Query Parameters**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| article_id | string | (必填) | 商品 ID |
| style | string | `product_description` | 文案风格 |

**style 可选值**

| 值 | 说明 |
|---|------|
| `product_description` | 商品描述（详细产品介绍） |
| `promotion` | 促销文案（折扣 + 行动号召） |
| `social_media` | 社交媒体文案（带话题标签） |

**示例请求**

```
POST /api/v1/tasks/copywriting?article_id=0126589003&style=promotion
```

**Response** — 同 2.1 通用任务响应格式，`results[0]` 包含：

| 字段 | 说明 |
|------|------|
| selected_copy | 选中的文案文本 |
| selected_style | 当前选中风格 |
| all_variants | 所有风格的文案变体 |
| reasoning | Agent 推理过程说明 |

---

### 2.3 智能补货

### `POST /api/v1/tasks/restock`

SupplyChain Agent 分析库存并生成补货建议。

**Query Parameters**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| article_id | string | (必填) | 商品 ID |
| forecast_days | int | 30 | 预测天数 (7-180) |

**示例请求**

```
POST /api/v1/tasks/restock?article_id=0126589003&forecast_days=30
```

**Response** — `results[0]` 包含：

| 字段 | 说明 |
|------|------|
| inventory_status | 当前库存状态（总量、各仓库分布） |
| restock_recommendation | 补货建议 |
| reasoning | ReAct 推理过程 |

**restock_recommendation 结构**

```json
{
  "should_reorder": true,
  "reorder_quantity": 500,
  "urgency": "high",
  "estimated_cost": 4250.00,
  "days_of_stock_remaining": 5,
  "supplier": {
    "name": "Guangzhou Fashion Manufacturing",
    "lead_time_days": 12,
    "min_order_quantity": 300,
    "reliability_score": 0.92
  }
}
```

| urgency | 含义 |
|---------|------|
| `high` | 已低于最低库存线，需立即补货 |
| `medium` | 库存不足覆盖预测期，建议补货 |
| `low` | 库存充足，暂不需要补货 |

---

### 2.4 清仓决策

### `POST /api/v1/tasks/clearance`

SupplyChain + Marketing Agent 协作，综合库存、竞品、销量决策是否清仓。

**Query Parameters**

| 参数 | 类型 | 说明 |
|------|------|------|
| article_id | string | 商品 ID (必填) |

**示例请求**

```
POST /api/v1/tasks/clearance?article_id=0142702004
```

**Response** — `results` 包含两个 Agent 结果：

1. SupplyChain Agent 的清仓分析：

| 字段 | 说明 |
|------|------|
| strategy | 清仓策略 |
| discount_pct | 折扣比例 (0-1) |
| reasoning | 决策原因 |
| overstock_ratio | 库存/预测比 |
| financials | 财务分析（原价、促销价、成本、折后利润率） |
| promo_copy | 自动生成的促销文案（strategy != hold 时） |

2. Marketing Agent 的文案结果

**strategy 值**

| 值 | 含义 | 折扣 |
|---|------|------|
| `deep_discount` | 库存 > 3x 预测，大幅清仓 | 40% |
| `moderate_discount` | 库存 > 2x 预测，适度促销 | 25% |
| `price_match` | 定价高于竞品，调价 | 按竞品差距 |
| `hold` | 暂不需要清仓 | 0% |

---

### 2.5 趋势分析

### `POST /api/v1/tasks/trend`

Data Agent 分析指定季节的时尚趋势。

**Query Parameters**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| season | string | `spring` | 季节 (spring/summer/autumn/winter) |

**示例请求**

```
POST /api/v1/tasks/trend?season=autumn
```

**Response** — `results[0].trend_data` 包含：

```json
{
  "success": true,
  "season": "autumn",
  "trending_colors": ["Burgundy", "Rust", "Olive", "Camel"],
  "trending_materials": ["Wool", "Cashmere", "Leather", "Corduroy"],
  "trending_styles": ["Tailored", "Layered", "Oversized", "Structured"],
  "trending_patterns": ["Plaid", "Houndstooth", "Animal Print"],
  "summary": "Autumn trends emphasize Burgundy and Rust tones..."
}
```

---

### 2.6 新品上架

### `POST /api/v1/tasks/launch`

Data + Marketing Agent 协作完成新品上架工作流：趋势匹配 + 文案生成。

**Query Parameters**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| article_id | string | (必填) | 商品 ID |
| season | string | `spring` | 目标季节 |

**示例请求**

```
POST /api/v1/tasks/launch?article_id=0126589003&season=spring
```

**Response** — `results` 包含两个 Agent 结果：

1. Data Agent：趋势分析数据
2. Marketing Agent：商品描述 + 社交媒体文案 + 所有变体

---

## 3. 技能 API (Skill Endpoints)

### 3.1 列出技能

### `GET /api/v1/skills`

列出所有已注册的 MCP 技能。

**Query Parameters**

| 参数 | 类型 | 说明 |
|------|------|------|
| level | string | 按级别过滤 (`L1` 或 `L2`) |
| tag | string | 按标签过滤 (如 `库存`, `文案`) |

**示例请求**

```
GET /api/v1/skills?level=L1
GET /api/v1/skills?tag=库存
```

**Response**

```json
{
  "total": 5,
  "skills": [
    {
      "name": "查询库存",
      "description": "查询指定商品的当前库存数量、仓库分布和可用状态",
      "tags": ["库存", "ERP", "供应链"],
      "examples": ["帮我查一下SKU 0108775015的库存"],
      "level": "L1"
    }
  ]
}
```

### 已注册技能列表

#### L1 原子技能

| 名称 | 描述 | 标签 |
|------|------|------|
| 查询库存 | 查询指定商品的当前库存数量、仓库分布和可用状态 | 库存, ERP, 供应链 |
| 销量预测 | 基于历史销售数据预测指定SKU的未来销量趋势 | 销量, 预测, 数据分析 |
| 竞品分析 | 分析同品类竞品的价格、销量和市场定位 | 竞品, 市场分析, 定价 |
| 趋势分析 | 分析指定季节或品类的时尚趋势 | 趋势, 时尚, 设计 |
| 文案生成 | 根据商品信息生成产品描述、促销文案或社交媒体文案 | 文案, 营销, 内容 |

#### L2 组合技能

| 名称 | 描述 | 组合的 L1 技能 |
|------|------|--------------|
| 智能补货 | 结合库存状态、销量预测和供应商信息，生成智能补货建议 | 查询库存 + 销量预测 |
| 清仓决策 | 综合库存积压、竞品价格和销量趋势，制定清仓策略并生成促销文案 | 查询库存 + 销量预测 + 竞品分析 + 文案生成 |
| 新品上架 | 结合时尚趋势分析和文案生成，为新品上架提供完整方案 | 趋势分析 + 文案生成 |

---

### 3.2 搜索技能

### `GET /api/v1/skills/search`

通过关键词语义搜索已注册技能。

**Query Parameters**

| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索关键词（必填） |

搜索范围：技能名称 (10分)、描述 (5分)、标签 (3分)、示例 (2分)，按分数排序。

**示例请求**

```
GET /api/v1/skills/search?q=补货
GET /api/v1/skills/search?q=文案
```

---

## 4. 数据浏览 API (Data Endpoints)

浏览系统种子数据（基于 H&M 数据集 schema）。

### 4.1 商品目录

### `GET /api/v1/data/articles`

获取所有商品 SKU 列表。

**Response**

```json
{
  "total": 20,
  "articles": [
    {
      "article_id": "0108775015",
      "product_code": "0108775",
      "prod_name": "Strap top",
      "product_type_name": "Vest top",
      "product_group_name": "Garment Upper body",
      "graphical_appearance_name": "Solid",
      "colour_group_name": "Black",
      "perceived_colour_value_name": "Dark",
      "perceived_colour_master_name": "Black",
      "department_name": "Jersey Basic",
      "index_name": "Ladieswear",
      "index_group_name": "Ladieswear",
      "section_name": "Womens Everyday Basics",
      "garment_group_name": "Jersey Basic",
      "detail_desc": "Jersey top with narrow shoulder straps."
    }
  ]
}
```

---

### 4.2 商品详情

### `GET /api/v1/data/articles/{article_id}`

获取单个商品的详细信息，包含库存和交易记录。

**示例**

```
GET /api/v1/data/articles/0126589003
```

**Response**

```json
{
  "article": { "article_id": "0126589003", "prod_name": "Cotton dress", ... },
  "inventory": [
    { "warehouse": "WH-EAST", "quantity": 15, "min_stock": 20, ... }
  ],
  "transactions": [
    { "t_dat": "2024-01-16", "customer_id": "C001", "price": 24.99, ... }
  ]
}
```

---

### 4.3 库存列表

### `GET /api/v1/data/inventory`

获取所有仓库的库存记录。

---

### 4.4 低库存预警

### `GET /api/v1/data/inventory/low-stock`

获取库存低于最低库存线的商品。

**Response**

```json
{
  "total": 3,
  "items": [
    {
      "article": { "article_id": "0126589003", "prod_name": "Cotton dress", ... },
      "inventory": { "warehouse": "WH-EAST", "quantity": 15, "min_stock": 20, ... }
    }
  ]
}
```

---

### 4.5 交易记录

### `GET /api/v1/data/transactions`

获取所有交易数据。

---

### 4.6 客户数据

### `GET /api/v1/data/customers`

获取客户画像数据。

---

### 4.7 供应商列表

### `GET /api/v1/data/suppliers`

获取供应商信息。

---

## 5. 错误处理

所有 API 在参数不合法时返回标准 FastAPI 422 错误：

```json
{
  "detail": [
    {
      "loc": ["query", "article_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

业务逻辑错误通过 `success: false` 标记：

```json
{
  "success": false,
  "message": "Article NONEXIST not found"
}
```

---

## 6. 系统架构流程

```
用户请求 → FastAPI Gateway
              ↓
         Master Agent (LangGraph StateGraph)
              ↓
         route → 根据 task_type 确定 Agent(s)
              ↓
         execute_agents → 依次执行子 Agent
         ├── Marketing Agent (ToT)  → 调用 L1/L2 技能
         ├── SupplyChain Agent (ReAct) → 调用 L1/L2 技能
         └── Data Agent (CoT)      → 调用 L1/L2 技能
              ↓
         aggregate → 汇总结果
              ↓
         返回 JSON 响应
```
