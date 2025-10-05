# downrisk-get

**股票值博率分析工具** - 基于下行波动率的损失风险评估系统

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 项目背景

本项目旨在建立一套**科学、可靠的值博率（Value-to-Risk Ratio）分析框架**，用于评估股票投资的风险收益比。

### 核心理念

传统的风险评估往往依赖个股历史数据，但存在以下问题：
- 个股历史数据可能不反映未来风险（如基本面已改变）
- 样本偏差（幸存者偏差、小样本）
- 无法评估新标的或转型公司

**本项目的创新方法**：
1. **使用行业ETF作为风险代理**：更稳定、更具代表性
2. **真实下行波动率**：只考虑下跌时的波动，更准确衡量损失风险
3. **Scheme C风险模型**：融合下行风险、系统性风险（β）、结构性风险（脆弱度）
4. **时间可调窗口**：支持3M/6M/12M/24M多种分析周期
5. **完整审计链路**：从原始数据到最终排名，每步可追溯

### 值博率定义

```
值博率 = 期望收益 ÷ 损失风险
```

- **值博率 > 2.0**：优秀投资机会
- **值博率 1.0-2.0**：良好
- **值博率 < 1.0**：需谨慎
- **值博率 < 0**：避免

---

## 🚀 快速开始

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/LpcPaul/downrisk-get.git
cd downrisk-get

# 2. 安装依赖
pip install -r requirements.txt
```

### 5分钟完成分析

```bash
# 运行分析（使用默认配置）
python3 -m volrisk.cli rank

# 查看结果
open output.xlsx  # macOS
# 或
start output.xlsx  # Windows
# 或
xdg-open output.xlsx  # Linux
```

就这么简单！系统会自动：
1. 获取7个行业ETF的历史数据（过去1年）
2. 计算每个行业的下行风险指标
3. 计算每家公司的值博率
4. 生成Excel报告和Markdown分析报告

---

## 📊 核心功能

### 1. Scheme C 风险模型（推荐）

```
损失风险 = 0.6 × σ_down + 0.3 × (β × σ_total) + 0.1 × Frag
```

**三大组成部分**：

1. **下行波动（60%权重）**
   - 基于日频半方差计算
   - 只考虑负收益，更准确
   - 年化处理（×√252）

2. **β × 总波动（30%权重）**
   - β：个股相对行业的敏感度
   - β > 1.0：比行业波动更剧烈（如周期股）
   - β < 1.0：比行业波动更平稳（如防御股）
   - 反映系统性风险暴露

3. **脆弱度（10%权重）**
   - 结构性风险加点（单位：百分点）
   - 评估因素：
     - 财务杠杆（净负债率）
     - 客户集中度
     - 监管/政策风险
     - 技术/商业化风险
     - 再融资压力

**脆弱度评级标准**：
- 0.5-1.5%：低脆弱（龙头、稳健）
- 1.5-3.0%：中等脆弱
- 3.0-5.0%：高脆弱（创新、烧钱）
- 5.0%+：极高脆弱

### 2. 时间可调窗口

```bash
# 分析过去2年
python3 -m volrisk.cli rank --period 2y

# 分析过去6个月
python3 -m volrisk.cli rank --period 6mo

# 指定具体日期
python3 -m volrisk.cli rank --start 2024-01-01 --end 2024-12-31
```

### 3. 期望收益评估方法论（详见 `docs/EXPECTED_RETURN_METHODOLOGY.md`）

本项目采用**基于基本面研究的期望收益评估框架**，核心原则：

#### **核心原则：用真实数据替代公式化假设**

传统方法的问题：
- ❌ 基于行业/赛道的一般性预期，过于公式化
- ❌ 未考虑个股的具体财务表现和盈利质量
- ❌ 忽略估值水平、竞争格局、行业前景等关键因素

**本项目的改进方法**：
- ✅ 基于公司实际2024年报业绩（营收、净利润、毛利率、净利率、现金流）
- ✅ 结合2025年分析师预测（营收/利润增速、PE估值、行业前景）
- ✅ 多维度评估：增长质量、盈利能力、估值水平、风险因素
- ✅ 动态调整：根据最新季报、指引、行业变化实时更新

#### **评估框架：三步法**

**步骤1：基础数据收集**
```yaml
# 示例：澜起科技
财务数据：
  2024年报：营收+59.2%，净利润+213.1%
  2025H1E：利润+89%至+106%

市场数据：
  DDR5全球份额：36.8%（第一）
  PE估值：合理区间

行业前景：
  DDR5渗透率持续提升
  新产品PCIe/MRCD/MDB营收8倍增长
```

**步骤2：多维度评估**
```
增长质量：
  - 营收增速 vs 利润增速
  - 毛利率、净利率趋势
  - 现金流状况
  - 销售费用占比

估值水平：
  - PE、PB相对历史分位
  - 与行业可比公司对比
  - 成长性匹配度（PEG）

风险因素：
  - 单品依赖风险
  - 客户集中度
  - 竞争加剧
  - 行业周期位置
  - 盈利质量下降
```

**步骤3：期望收益确定**
```yaml
companies:
  # 高增长（28-40%）：业绩超预期 + 行业景气 + 估值合理
  - name: "澜起科技"
    sector: "SEMI"
    expected_return: 0.40  # 40%
    # 理由：2024利润+213%，DDR5全球第一，2025H1E+89-106%

  # 稳健增长（20-25%）：业绩稳健 + 盈利质量高
  - name: "腾讯控股"
    sector: "INTERNET"
    expected_return: 0.20  # 20%
    # 理由：2024营收+8%，利润+41%靠成本控制，业务成熟

  # 低增长/承压（<15%）：营收利润双降 + 行业需求疲软
  - name: "长飞光纤"
    sector: "SEMI"
    expected_return: 0.12  # 12%
    # 理由：2024营收-8.65%，利润-47.91%，行业承压
```

#### **实战案例：9家公司分析**

详见 `FUNDAMENTALS_ANALYSIS_REPORT.md`，核心发现：

| 公司 | 初始预期 | 基本面预期 | 调整幅度 | 调整理由 |
|------|----------|------------|----------|----------|
| 澜起科技 | 35% | **40%** | **+5%** | DDR5超预期，2025H1E利润+89-106% |
| 联想集团 | 18% | **22%** | **+4%** | AI PC/AI服务器驱动，业绩超预期 |
| 巨子生物 | 35% | 25% | **-10%** | 盈利质量下降，单品风险，竞争加剧 |
| 三花智控 | 28% | 20% | **-8%** | 估值不便宜（PE~35x），调整预期 |
| 长飞光纤 | 20% | 12% | **-8%** | 营收利润双降，行业承压 |

**排名变化**：
- 🥇 澜起科技：第4名 → 第1名（VTR 1.45）
- 🥈 中金公司：维持第2名（VTR 1.43）
- 🥉 联想集团：维持第3名（VTR 1.34）
- ⚠️ 三花智控：第1名 → 第4名（VTR 1.17）

#### **配置示例**

```yaml
companies:
  # 直接指定期望收益（推荐）
  - name: "澜起科技"
    sector: "SEMI"
    expected_return: 0.40  # 40% - 基于详细基本面研究
    risk:
      mode: "SchemeC"
      beta: 1.15
      frag: 2.5
```

**详细方法论文档**：
- `docs/EXPECTED_RETURN_METHODOLOGY.md` - 完整评估框架
- `FUNDAMENTALS_ANALYSIS_REPORT.md` - 9家公司实战案例
- `config/companies_analysis.yml` - 带详细注释的配置示例

### 4. 混合行业暴露

对于多行业暴露的公司（如紫金矿业）：

```yaml
- name: "紫金矿业"
  sector_mix:
    NONFER: 0.6  # 60%有色金属
    GOLD: 0.4    # 40%黄金
  expected_return: 0.18
  risk:
    mode: "SchemeC"
    beta: 0.95  # 混合配置，波动略低
    frag: 1.5   # 脆弱度：商品价格波动
```

系统自动按权重混合各行业的风险指标。

---

## 🏗️ 项目结构

```
downrisk-get/
├── volrisk/                    # 核心包
│   ├── __init__.py
│   ├── data.py                # 数据获取（yfinance + parquet缓存）
│   ├── metrics.py             # 指标计算（σ_down、σ_total、MDD）
│   ├── beta.py                # β回归计算（OLS/Huber）
│   ├── sector.py              # 行业ETF处理
│   ├── expected.py            # 期望收益计算
│   ├── risk.py                # 风险计算（SchemeC/SemiMDD）
│   ├── ranker.py              # 排名与导出
│   └── cli.py                 # CLI接口
│
├── config/                     # 配置文件
│   ├── sectors.yml            # 7个行业ETF配置
│   ├── companies.yml          # 原始7家公司配置
│   └── companies_v2.yml       # v2.0框架13家公司配置
│
├── docs/                       # 文档
│   ├── QUICKSTART.md          # 快速上手指南
│   ├── SCHEME_C_ANALYSIS.md   # Scheme C分析报告（7家公司）
│   ├── ANALYSIS_SUMMARY.md    # 原始分析报告
│   └── CALCULATION_COMPARISON.md  # 计算验证报告（13家公司）
│
├── tests/                      # 单元测试
│   ├── test_metrics.py
│   ├── test_beta.py
│   └── test_risk.py
│
├── .cache/                     # 数据缓存（自动创建）
├── output.xlsx                 # 默认输出文件
├── requirements.txt            # 依赖清单
├── pyproject.toml             # 项目配置
└── README.md
```

---

## 🔧 CLI 命令详解

### 1. `rank` - 主命令（计算值博率并排名）

```bash
# 使用默认配置
python3 -m volrisk.cli rank

# 使用v2.0配置（13家公司）
python3 -m volrisk.cli rank --companies config/companies_v2.yml

# 自定义输出
python3 -m volrisk.cli rank --output my_analysis.xlsx

# 指定时间范围
python3 -m volrisk.cli rank --period 2y
python3 -m volrisk.cli rank --start 2024-01-01 --end 2024-12-31

# 完整参数
python3 -m volrisk.cli rank \
  --companies config/companies_v2.yml \
  --sectors config/sectors.yml \
  --output v2_results.xlsx \
  --period 1y \
  --force  # 强制刷新缓存
```

### 2. `fetch` - 获取ETF数据

```bash
# 获取单个ETF
python3 -m volrisk.cli fetch 512480.SS

# 指定日期范围
python3 -m volrisk.cli fetch 512480.SS --start 2024-01-01 --end 2024-12-31

# 强制刷新
python3 -m volrisk.cli fetch 512480.SS --force
```

### 3. `calc-sector` - 计算行业指标

```bash
# 计算所有行业风险指标
python3 -m volrisk.cli calc-sector

# 使用自定义配置
python3 -m volrisk.cli calc-sector --config config/sectors.yml --period 2y
```

### 4. `clear-cache` - 清除缓存

```bash
# 清除所有缓存
python3 -m volrisk.cli clear-cache

# 只清除特定ticker
python3 -m volrisk.cli clear-cache --ticker 512480.SS
```

---

## 📐 核心算法详解

### 下行波动率（σ_down）

只考虑低于MAR（最低可接受收益，默认为0）的收益：

```python
def downside_volatility(returns, mar=0.0, annualize=True):
    """
    计算下行波动率（日频半方差年化）

    公式：
    1. downside = min(returns - mar, 0)  # 只保留负偏差
    2. semi_variance = mean(downside²)
    3. σ_down = sqrt(semi_variance)
    4. if annualize: σ_down *= sqrt(252)
    """
    downside = np.minimum(returns - mar, 0.0)
    semi_variance = np.mean(downside ** 2)
    semi_std = np.sqrt(semi_variance)
    if annualize:
        semi_std = semi_std * np.sqrt(252)  # 252个交易日
    return semi_std
```

**关键点**：
- 不使用 σ_total / √2 的近似公式
- 基于真实日频数据计算
- 年化处理确保可比性

### β系数计算

```python
def beta_ols(stock_returns, sector_returns, min_overlap=50):
    """
    OLS回归计算β系数

    模型：stock_return = α + β × sector_return + ε

    β = Cov(stock, sector) / Var(sector)
    """
    # 1. 对齐时间序列
    aligned = pd.concat([stock_returns, sector_returns], axis=1).dropna()

    # 2. 最小样本要求
    if len(aligned) < min_overlap:
        return 1.0  # 默认β

    # 3. 计算协方差矩阵
    cov_matrix = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
    var_sector = cov_matrix[0, 0]
    cov_stock_sector = cov_matrix[0, 1]

    # 4. β = Cov / Var
    beta = cov_stock_sector / var_sector

    return beta
```

**可选方法**：
- OLS（普通最小二乘）：标准方法
- Huber（鲁棒回归）：对异常值更稳健

### 最大回撤（MDD）

```python
def maximum_drawdown(prices):
    """
    计算最大回撤

    公式：
    1. cummax = 累计最高点
    2. drawdown = (price / cummax) - 1
    3. MDD = min(drawdown)
    """
    cummax = prices.cummax()
    drawdown = (prices / cummax) - 1.0
    mdd = drawdown.min()
    return abs(mdd)
```

---

## 📋 配置文件详解

### sectors.yml - 行业ETF配置

```yaml
sectors:
  # 半导体
  SEMI:
    tickers: ["512480.SS"]  # 半导体50ETF（上交所）
    weights: [1.0]

  # 中概互联网
  INTERNET:
    tickers: ["513050.SS"]  # 中概互联网ETF
    weights: [1.0]

  # 有色金属
  NONFER:
    tickers: ["512400.SS"]  # 有色金属ETF
    weights: [1.0]

  # 医疗器械
  MEDDEV:
    tickers: ["159898.SZ"]  # 医疗器械ETF（深交所）
    weights: [1.0]

  # 恒生生物科技
  BIOHK:
    tickers: ["159892.SZ"]  # 恒生生科ETF
    weights: [1.0]

  # 主要消费
  CONSUMER:
    tickers: ["159928.SZ"]  # 消费ETF
    weights: [1.0]

  # 黄金
  GOLD:
    tickers: ["518850.SS"]  # 黄金ETF
    weights: [1.0]
```

**代码格式说明**：
- 上交所：`.SS` 后缀（如 `512480.SS`）
- 深交所：`.SZ` 后缀（如 `159898.SZ`）
- 港股：`.HK` 后缀（如 `2228.HK`）

### companies_v2.yml - 公司配置（v2.0框架）

```yaml
companies:
  # 1. 建滔积层板 - CCL板块领军
  - name: "建滔积层板"
    sector: "NONFER"  # 材料链，用有色金属风险代理
    expected_return: 0.30  # 30% - 高端化+涨价执行
    risk:
      mode: "SchemeC"
      beta: 1.05  # 材料周期，略高于行业
      frag: 2.0   # 脆弱度：需求波动

  # 2. 澜起科技 - 半导体内存接口
  - name: "澜起科技"
    sector: "SEMI"
    expected_return: 0.35  # 35% - DDR5放量+份额提升
    risk:
      mode: "SchemeC"
      beta: 1.15  # 半导体周期股，高敏感
      frag: 2.5   # 脆弱度：行业周期+客户集中

  # 7. 紫金矿业 - 资源综合（混合行业）
  - name: "紫金矿业"
    sector_mix:
      NONFER: 0.6  # 60%有色
      GOLD: 0.4    # 40%黄金
    expected_return: 0.18  # 18% - 资源价格温和+产能释放
    risk:
      mode: "SchemeC"
      beta: 0.95  # 混合配置，低敏感
      frag: 1.5   # 脆弱度：商品价格波动

  # ... 更多公司
```

**v2.0收益框架说明**：

期望收益基于"量×价×结构×成本→盈利增长×执行概率"的中性场景（Base）

**调整原则**：
1. 高端化+涨价执行力强 → 建滔30%、澜起35%
2. 结构提升+周期复苏 → 巨石24%、生益28%、晶泰30%
3. 稳健增长 → 阿里25%、金诚信22%、长电20%
4. 温和增长 → 紫金18%
5. 承压/不确定性 → 中宠15%、中材15%、江西铜15%、锦波12%

**可选调整**：
- 生益科技：如改用NONFER风险，值博率将从1.07升至约1.35
- 所有收益可根据最新催化调整（建议设置Bear/Base/Bull三档）

---

## 📊 输出文件说明

### output.xlsx - Excel报告

包含完整的分析结果：

| 列名 | 说明 |
|------|------|
| 排名 | 按值博率降序 |
| 公司名称 | 标的名称 |
| 行业代理 | 风险代理ETF（可能是混合） |
| σ总波动 | 行业总波动率 |
| σ下行 | 行业下行波动率 |
| MDD | 行业最大回撤 |
| ER原始 | 原始期望收益 |
| ER执行后 | 考虑执行概率后的期望收益 |
| 损失风险 | Scheme C计算的总风险 |
| 值博率 | ER执行后 ÷ 损失风险 |
| Beta | β系数（仅SchemeC模式） |

### ANALYSIS_SUMMARY.md - 分析报告

自动生成的Markdown报告，包含：
- 🎯 Top 3投资机会
- 📉 行业风险全景
- ⚠️ 风险警示
- 💡 投资组合建议
- 📝 免责声明

---

## 🔬 方法论验证

### 计算验证报告

详见 `CALCULATION_COMPARISON.md`，该报告对比了：
- 用户手工计算的13家公司结果
- 本系统自动计算的结果
- 差异分析和原因解释

**验证结果**：
- 13家公司中12家完全一致（风险差异 < 0.03%）
- 1家有微小差异（中国巨石，风险差1.39%，源于β/Frag参数差异）
- **总体一致性：92.3%**

### Scheme C模型验证

**手工验证示例（澜起科技）**：

```
配置参数：
- sector: SEMI
- expected_return: 0.35 (35%)
- beta: 1.15
- frag: 2.5 (%)

SEMI行业指标（实测）：
- σ_down = 0.2286
- σ_total = 0.3924

Scheme C计算：
损失风险 = 0.6 × σ_down + 0.3 × (β × σ_total) + 0.1 × (Frag/100)
         = 0.6 × 0.2286 + 0.3 × (1.15 × 0.3924) + 0.1 × 0.025
         = 0.13716 + 0.135276 + 0.0025
         = 0.274936
         ≈ 27.50%

值博率 = 0.35 / 0.2750 = 1.27

✅ 与系统输出完全一致
```

---

## 📚 延伸阅读

### 推荐文档阅读顺序

1. **新手入门**：
   - `QUICKSTART.md` - 5分钟快速上手
   - `README.md` - 本文档（完整功能介绍）

2. **理解结果**：
   - `SCHEME_C_ANALYSIS.md` - 7家公司的完整分析报告
   - `ANALYSIS_SUMMARY.md` - 原始分析报告

3. **验证方法**：
   - `CALCULATION_COMPARISON.md` - 计算验证报告（13家公司）

4. **配置实例**：
   - `config/companies.yml` - 原始7家公司配置
   - `config/companies_v2.yml` - v2.0框架13家公司配置

### 行业风险参考（2024-09-30至2025-09-30实测）

| 行业 | σ下行 | σ总 | MDD | 推荐β | 典型脆弱度 |
|------|-------|-----|-----|-------|-----------|
| 黄金 | 10.76% | 15.98% | 11.64% | 0.8-1.0 | 0.5-1.5% |
| 消费 | 15.93% | 21.16% | 18.52% | 0.9-1.1 | 1.5-3.0% |
| 有色 | 19.78% | 27.67% | 17.06% | 1.0-1.3 | 2.0-4.0% |
| 医械 | 20.15% | 27.41% | 23.96% | 0.9-1.2 | 3.0-5.0% |
| 互联网 | 21.19% | 31.32% | 22.32% | 1.0-1.2 | 2.0-4.0% |
| 生科 | 22.64% | 34.10% | 19.36% | 1.2-1.5 | 4.0-6.0% |
| 半导体 | 22.86% | 39.24% | 19.39% | 1.0-1.3 | 2.0-4.0% |

---

## 🎯 设计理念与创新点

### 为什么不用个股历史数据？

传统方法的问题：
1. **样本偏差**：历史数据可能不反映未来（基本面已改变）
2. **幸存者偏差**：只看到活下来的公司
3. **小样本**：新标的、转型公司缺乏足够历史
4. **极端事件**：个股可能经历一次性极端波动

**本项目的解决方案**：
- 使用行业ETF作为风险代理
- ETF更稳定、更具代表性
- 避免个股特殊性干扰
- 适用于新标的和转型公司

### Scheme C vs SemiMDD

**Scheme C优势**（推荐）：
✅ 基于真实下行波动（60%权重）
✅ 包含β系数，反映系统性风险
✅ 脆弱度量化结构性风险
✅ 不受MDD影响，对高成长更友好
✅ 权重可调，适应不同风险偏好

**SemiMDD特点**：
- 包含MDD（最大回撤）
- 对极端下跌更敏感
- 适合保守投资者
- 可能低估高成长股的价值

**建议**：成长股用Scheme C，防御股可用SemiMDD

### 时间窗口的选择

- **3M（3个月）**：捕捉短期波动，适合高频调整
- **6M（6个月）**：平衡短期与长期，适合季度复盘
- **12M（12个月）**：标准窗口，反映完整年度周期（推荐）
- **24M（24个月）**：长期趋势，平滑短期噪音

**默认使用12M**，因为：
- 包含完整的四个季度
- 覆盖大部分企业财报周期
- 数据充足但不过时

---

## 🔄 后续优化方向

### 1. 实测β回归（已实现）
- 基于个股vs行业历史数据回归计算真实β
- 支持OLS和Huber鲁棒回归

### 2. 场景法期望收益（v2.0已采用）
- Bear/Base/Bull三档概率加权
- 基于"量×价×结构×成本"的业务驱动分析

### 3. 滚动窗口分析（计划中）
- 3M/6M/12M/24M多时间尺度验证
- 观察风险指标的稳定性

### 4. 敏感性分析（计划中）
- β±0.1、脆弱度±1%的影响
- 参数不确定性的容忍度

### 5. 蒙特卡洛模拟（计划中）
- 参数不确定性下的值博率分布
- 置信区间估计

---

## ⚠️ 使用注意事项

### 数据质量

1. **ETF数据完整性**：
   - 新上市的ETF可能缺少足够历史数据
   - 建议至少1年以上数据
   - 缺失数据会在输出中标注

2. **网络连接**：
   - yfinance需要稳定的网络连接
   - 建议首次运行后使用缓存
   - 遇到问题使用 `--force` 强制刷新

### 参数设定

1. **β系数**：
   - 默认β=1.0（与行业同步）
   - 周期股建议β>1.0
   - 防御股建议β<1.0
   - 可通过历史数据回归验证

2. **脆弱度**：
   - 需要基于基本面分析
   - 考虑财务杠杆、客户集中度、监管风险等
   - 建议范围：0.5%-5.0%

3. **期望收益**：
   - 不要过度乐观
   - 建议使用中性场景（Base）
   - 可设置Bear/Base/Bull三档

### 风险提示

⚠️ **本工具仅供参考，不构成投资建议**

- 历史数据不代表未来表现
- 模型假设可能与实际偏差
- 请结合自身风险承受能力
- 建议分散投资，不要单一押注

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/LpcPaul/downrisk-get.git
cd downrisk-get

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black volrisk/ tests/
ruff check volrisk/
```

### 提交要求

- 代码遵循PEP 8规范
- 新功能需要添加测试
- 更新相关文档
- 提交信息清晰明确

---

## 📞 联系方式

- **GitHub**: [@LpcPaul](https://github.com/LpcPaul)
- **项目主页**: https://github.com/LpcPaul/downrisk-get
- **Issues**: https://github.com/LpcPaul/downrisk-get/issues

---

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

## 🙏 致谢

- **数据来源**：[yfinance](https://github.com/ranaroussi/yfinance)
- **计算框架**：基于现代投资组合理论和下行风险理论
- **灵感来源**：Peter Bernstein的《风险》、Harry Markowitz的投资组合理论

---

**最后更新**: 2025-10-05
**版本**: v1.0.0
**维护者**: @LpcPaul

---

**⭐ 如果这个项目对你有帮助，请给个Star！**
