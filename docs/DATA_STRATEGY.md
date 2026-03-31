# 数据策略 - FashionAgent

## 主数据集：H&M Personalized Fashion Recommendations

来源：Kaggle - [H&M Personalized Fashion Recommendations](https://www.kaggle.com/c/h-and-m-personalized-fashion-recommendations/data)

### 为什么选择这个数据集

| 维度 | H&M 数据集 | 项目需求 | 匹配度 |
|------|-----------|---------|-------|
| 商品数据 | 105,542 SKU，25 个字段 | SKU 管理、Entity Memory | ✅ 完美 |
| 交易数据 | 31,788,324 条购买记录 | 销量预测、补货决策 | ✅ 完美 |
| 用户数据 | 1,371,980 用户画像 | 用户偏好分析 | ✅ 完美 |
| 商品图片 | 105,000+ 张商品图 | 视觉 Agent 参考 | ✅ 完美 |
| 品类层级 | 产品组/部门/分区/指数 4 级分类 | 知识图谱构建 | ✅ 完美 |
| 颜色体系 | 颜色组/感知色值/感知主色 3 维 | 设计 Agent 分析 | ✅ 完美 |
| 时间跨度 | 2018-2020 购买历史 | 趋势分析、季节性模式 | ✅ 完美 |

### 数据表结构

#### articles.csv (商品表 - 105,542 行)

```
article_id              - 商品唯一ID (如: 0108775015)
product_code            - 基础产品代码
prod_name               - 产品名称 (如: "Strap top")
product_type_no         - 产品类型编号
product_type_name       - 产品类型名称 (如: "Vest top")
product_group_name      - 产品组名 (如: "Garment Upper body")
graphical_appearance_no - 图案外观编号
graphical_appearance_name - 图案名称 (如: "Solid", "Stripe")
colour_group_code       - 颜色组代码
colour_group_name       - 颜色组名 (如: "Black", "White")
perceived_colour_value_id - 感知色值ID
perceived_colour_value_name - 感知色值 (如: "Dark", "Light")
perceived_colour_master_id - 感知主色ID
perceived_colour_master_name - 感知主色 (如: "Black", "Blue")
department_no           - 部门编号
department_name         - 部门名称 (如: "Jersey Basic")
index_code              - 指数代码
index_name              - 指数名称 (如: "Ladieswear")
index_group_no          - 指数组编号
index_group_name        - 指数组名 (如: "Ladieswear")
section_no              - 分区编号
section_name            - 分区名称 (如: "Womens Everyday Basics")
garment_group_no        - 服装组编号
garment_group_name      - 服装组名 (如: "Jersey Basic")
detail_desc             - 详细描述 (如: "Jersey top with narrow shoulder straps.")
```

#### customers.csv (用户表 - 1,371,980 行)

```
customer_id             - 用户唯一ID (哈希)
FN                      - 是否活跃 (1.0/NaN)
Active                  - 会员活跃状态
club_member_status      - 会员状态 (ACTIVE/PRE-CREATE/LEFT CLUB)
fashion_news_frequency  - 时尚资讯频率 (Regularly/Monthly/NONE)
age                     - 年龄
postal_code             - 邮编 (哈希)
```

#### transactions_train.csv (交易表 - 31,788,324 行)

```
t_dat                   - 交易日期 (如: 2018-09-20)
customer_id             - 用户ID
article_id              - 商品ID
price                   - 价格
sales_channel_id        - 销售渠道 (1=线上, 2=线下)
```

### 补充数据（合成生成）

H&M 数据集缺少库存、物流、竞品数据，我们用合成数据补充：

| 补充数据 | 生成方式 | 关联字段 |
|---------|---------|---------|
| 库存数据 (inventory) | 基于销量反推合理库存 | article_id |
| 仓库数据 (warehouses) | 模拟 3 个仓库分布 | warehouse_id |
| 物流数据 (logistics) | Faker 生成物流轨迹 | order_id |
| 竞品数据 (competitors) | 基于真实数据加噪声 | product_type |
| 用户评价 (reviews) | LLM 生成 + 评分 | article_id, customer_id |
| 供应商 (suppliers) | 按品类分配模拟供应商 | department_name |

---

## 项目中的数据用法

为了让项目开箱即用（不依赖 Kaggle 下载），我们准备了两套方案：

### 方案 A：Seed Data（默认）

项目内置一个精简的种子数据集（~500 条 SKU），覆盖主要品类，可直接运行。

### 方案 B：Full Dataset（可选）

用户下载 H&M 数据集后，运行导入脚本加载完整数据。

```bash
# 下载 H&M 数据集到 data/raw/
kaggle competitions download -c h-and-m-personalized-fashion-recommendations

# 导入到系统
python scripts/import_hm_data.py --data-dir data/raw/ --sample-size 10000
```
