# V7.3 完整执行流程 (端到端) - 更新版

**目标**: 从零开始，完整执行VTR股票估值分析的全流程

**时间投入**: 首次执行约8-12小时，后续季度更新约4-6小时

**更新内容**: 修正新增公司流程顺序，强调先确定细分行业归属再提取σ_down数据

---

## 📋 流程总览

```
⚠️ 数据时效性要求 (贯穿全流程)
  ├─ Yahoo Finance估值数据: <7天 (通常<1小时)
  ├─ 公司财报数据: 最新季报/年报 (优先H1/Q3财报)
  ├─ 行业信息: ≤3个月
  └─ 每次执行必须标注数据采集时间

Phase 0: 信息收集 (4-6小时) ⚠️ 数据时效性核心阶段
  ├─ Step 0.1: 获取估值数据 (15分钟)
  │   └─ 数据源: Yahoo Finance API (实时)
  ├─ Step 0.2: 搜集财报数据 (2-3小时)
  │   ├─ 财务数据: 上市公司公告、Wind/Choice数据库
  │   ├─ 未来预期事件: 券商研报 (近3个月)、公司调研纪要、行业专家访谈
  │   └─ 数据时效性: ≤3个月
  ├─ Step 0.3: 搜集行业数据 (1-2小时)
  │   └─ 行业数据时效性: ≤3个月
  └─ Step 0.4: 计算期望收益 (1-2小时)
      └─ Bear/Base/Bull场景分析
       ↓
Phase 1: 风险计算 (30分钟)
  ├─ Step 1.1: 确定公司细分行业归属 ⚠️ 新增步骤
  └─ Step 1.2: 计算/提取细分行业σ_down
       ↓
Phase 2: VTR计算 (30分钟)
  ├─ Step 2.1: 建立公司-细分行业映射
  └─ Step 2.2: 计算VTR并排名
       ↓
Phase 3: 生成完整报告 (1小时)
  ├─ Step 3.1: 生成VTR排名报告 (排名结论置于最前)
  ├─ Step 3.2: 详细展示每家公司VTR计算过程
  └─ Step 3.3: 标注所有数据来源与时效性
```

---

## 🆕 新增公司快速流程 (针对已有14家基础上新增)

**场景**: 已完成原14家公司分析，现需新增9家半导体材料/设备公司

**执行顺序** (关键修正):

```
Step 1: 收集估值数据 (15分钟)
  └─ 执行: python3 scripts/fetch_valuation_data.py
  └─ 输出: /tmp/9companies_valuation.csv
  └─ 检查: PE/PB/ROE/Beta等9项指标完整

Step 2: 搜集财报和行业数据 (2-3小时)
  ├─ 财务数据: 2025年H1财报、业绩亮点、分部收入、毛利率
  ├─ 行业数据: 细分行业景气度、技术趋势、竞争格局
  ├─ 未来预期事件 (影响收益预期):
  │   ├─ 催化剂: 扩产计划、技术升级、客户突破、政策利好、并购整合
  │   └─ 风险: 产能过剩、技术风险、客户流失、政策风险、竞争加剧、原材料风险
  ├─ 数据源: 券商研报 (近3个月内)、公司调研纪要、行业专家访谈、公司公告
  └─ 输出: 每家公司的业务特征描述 + 未来预期事件清单

Step 3: 确定细分行业归属 ⚠️ 关键步骤，必须在提取σ_down之前
  ├─ 分析每家公司主营业务构成
  ├─ 映射到13个细分行业 (参考docs/PRECISE_INDUSTRY_SEGMENTATION_V7.md)
  ├─ 多业务公司确定利润权重
  └─ 输出: 公司-细分行业映射表

  示例:
    安集科技 → 半导体材料-CMP (100%)
    长川科技 → 半导体设备-测试 (100%)
    三环集团 → 半导体材料-MLCC (100%)

Step 4: 提取细分行业σ_down数据 ⚠️ 在确定归属后执行
  ├─ 检查data/subindustry_sigma_down.csv是否已有数据
  ├─ 已有: 直接提取对应ETF的σ_down
  ├─ 未有: 执行scripts/calculate_subindustry_sigma_down.py
  └─ 输出: 每家公司对应的σ_down值

  示例:
    半导体材料 (516020.SS) → σ_down = 21.76%
    半导体设备 (516290.SS) → σ_down = 21.66%

Step 5: 计算期望收益 (1-2小时)
  ├─ 基于财报和行业分析，进行Bear/Base/Bull场景分析
  ├─ 单业务公司: 期望收益 = 行业趋势
  ├─ 多业务公司: 期望收益 = Σ(分部收益 × 利润权重)
  └─ 输出: 每家公司1年期期望收益

Step 6: 计算VTR并排名 (15分钟)
  ├─ VTR = 期望收益 / σ_down
  ├─ 合并原14家 + 新9家 = 23家完整排名
  └─ 输出: 完整VTR排名表

Step 7: 生成分析报告 (30分钟)
  ├─ 新增公司整体表现分析
  ├─ Top 10排名变化分析
  ├─ 细分行业对比分析
  └─ 投资组合配置建议更新
```

---

## Phase 1: 风险计算 (更新版)

### Step 1.1: 确定公司细分行业归属 ⚠️ 新增步骤

**目标**: 在提取σ_down之前，先明确每家公司的细分行业归属

**执行清单**:

```yaml
单业务公司:
  1. 分析公司主营业务产品线
  2. 参考docs/PRECISE_INDUSTRY_SEGMENTATION_V7.md确定细分行业
  3. 记录到映射表

  示例:
    安集科技:
      主营: CMP抛光液 + 功能性湿化学品
      细分行业: 半导体材料-CMP
      业务占比: 100%

多业务公司:
  1. 从财报提取分部收入/利润数据
  2. 计算各业务利润权重
  3. 为每个业务分部确定细分行业
  4. 记录到映射表

  示例:
    紫金矿业:
      业务1: 铜矿开采 (60%利润) → 铜矿开采
      业务2: 黄金开采 (40%利润) → 黄金开采
```

**输出文件**: `data/company_subindustry_mapping.yml`

```yaml
companies:
  安集科技:
    subindustry: "半导体材料-CMP"
    exposure: 1.0
    notes: "CMP抛光液全球市占率10%，核心原材料自产"

  紫金矿业:
    subindustry_mix:
      铜矿开采: 0.60
      黄金开采: 0.40
    notes: "铜金一体化矿业，60%铜+40%黄金(利润权重)"
```

**检查标准**:
- ✅ 所有公司都有明确的细分行业归属
- ✅ 多业务公司权重之和 = 1.0
- ✅ 细分行业名称与docs/PRECISE_INDUSTRY_SEGMENTATION_V7.md一致

---

### Step 1.2: 计算/提取细分行业σ_down ⚠️ 在Step 1.1之后执行

**目标**: 根据Step 1.1确定的细分行业归属，获取对应的σ_down数据

**执行逻辑**:

```python
# 伪代码
def get_sigma_down(company_name):
    # Step 1: 读取公司细分行业归属
    mapping = load_company_subindustry_mapping()
    subindustries = mapping[company_name]['subindustry']

    # Step 2: 检查是否已有σ_down数据
    sigma_data = load_subindustry_sigma_down()

    # Step 3: 如果已有，直接提取
    if subindustry in sigma_data:
        return sigma_data[subindustry]['sigma_down']

    # Step 4: 如果没有，需要计算新ETF的σ_down
    else:
        print(f"警告: {subindustry} 缺少σ_down数据")
        print(f"请执行: python3 scripts/calculate_subindustry_sigma_down.py")
        return None
```

**执行命令** (仅在缺少数据时):

```bash
# 如果data/subindustry_sigma_down.csv缺少某些细分行业
python3 scripts/calculate_subindustry_sigma_down.py

# 检查输出
cat data/subindustry_sigma_down.csv
```

**输出示例**:

```csv
subindustry,etf_code,sigma_down,sigma_total,days
半导体材料-CMP,516020.SS,0.2176,0.2265,244
半导体设备-测试,516290.SS,0.2166,0.3284,242
```

**检查标准**:
- ✅ 所有公司涉及的细分行业都有σ_down数据
- ✅ σ_down在10%-30%合理区间
- ✅ ETF历史数据≥200天

---

## Phase 2: VTR计算 (更新版)

### Step 2.1: 建立公司-细分行业映射

**前置条件**:
- ✅ Phase 0完成 (有公司期望收益数据)
- ✅ Step 1.1完成 (有细分行业归属)
- ✅ Step 1.2完成 (有细分行业σ_down数据)

**配置文件**: `scripts/build_company_subindustry_mapping.py`

**关键配置**:

```python
# 1. 细分行业σ_down数据 (从Step 1.2提取)
SUBINDUSTRY_SIGMA_DOWN = {
    '半导体材料-CMP': {
        'etf_code': '516020.SS',
        'sigma_down': 0.2176,  # ← 从data/subindustry_sigma_down.csv提取
    },
    '半导体设备-测试': {
        'etf_code': '516290.SS',
        'sigma_down': 0.2166,
    },
}

# 2. 公司-细分行业映射 (从Step 1.1提取)
COMPANY_SUBINDUSTRY_EXPOSURE = {
    '安集科技': {
        'exposures': [('半导体材料-CMP', 1.0)],  # ← 从Step 1.1提取
        'expected_return_1y': 0.140,  # ← 从Phase 0 Step 0.3提取
        'notes': 'CMP抛光液全球市占率10%'
    },

    '紫金矿业': {
        'exposures': [
            ('铜矿开采', 0.60),
            ('黄金开采', 0.40),
        ],
        'expected_return_1y': -0.240,
        'notes': '铜金一体化矿业'
    },
}
```

---

### Step 2.2: 计算VTR并排名

**执行命令**:

```bash
python3 scripts/build_company_subindustry_mapping.py
```

**计算公式**:

```python
# 单业务公司
VTR = expected_return_1y / sigma_down

# 多业务公司
weighted_sigma_down = Σ(分部σ_down × 利润权重)
VTR = expected_return_1y / weighted_sigma_down
```

**输出文件**: `data/company_subindustry_vtr.csv`

```csv
排名,公司,VTR,期望收益,σ_down,细分行业,评级
1,ASMPT,0.79,17.1%,21.66%,半导体设备-后道封装,⭐优秀
2,川恒股份,0.79,18.0%,22.79%,磷化工-LFP,⭐优秀
3,安集科技,0.64,14.0%,21.76%,半导体材料-CMP,⭐优秀
...
```

**检查标准**:
- ✅ 所有公司都有VTR排名
- ✅ VTR = 期望收益 / σ_down (手工验证至少3家)
- ✅ 多业务公司σ_down为加权值

---

## 🔄 新增公司案例: 9家半导体公司完整执行记录

### 实际执行记录 (2025-10-08)

```yaml
Step 1: 收集估值数据 ✅
  执行时间: 2025-10-08 (数据采集时间: 2025-10-07)
  脚本: scripts/fetch_valuation_data.py
  输出: /tmp/9companies_valuation.csv
  状态: 9家公司估值数据完整

Step 2: 搜集财报和行业数据 ✅
  数据来源: V7.3_COMPLETE_RANKING_23COMPANIES_2025Q3.md
  时效性: 2025年H1财报 (1.5-3个月)
  状态: 完整

Step 3: 确定细分行业归属 ✅
  分析结果:
    - 7家半导体材料公司 → 516020.SS
    - 2家半导体设备公司 → 516290.SS
  输出: /tmp/9companies_subindustry_mapping.md
  状态: 归属清晰，无多业务公司

Step 4: 提取细分行业σ_down数据 ✅
  数据来源: data/subindustry_sigma_down.csv (已有数据)
  结果:
    - 半导体材料: σ_down = 21.76%
    - 半导体设备: σ_down = 21.66%
  输出: /tmp/9companies_sigma_down.md
  状态: 数据完整，无需重新计算

Step 5: 计算期望收益 ✅
  数据来源: V7.3_COMPLETE_RANKING_23COMPANIES_2025Q3.md
  方法: Bear/Base/Bull场景分析
  结果:
    - 安集科技: +14.0% (最高)
    - 长川科技: +8.5%
    - 三环集团: +8.0%
    - ... (共9家)
  状态: 期望收益合理 (5%-14%)

Step 6: 计算VTR并排名 ✅
  计算结果:
    - 安集科技: VTR 0.64 (23家中排名第3)
    - 长川科技: VTR 0.39 (23家中排名第5)
    - 7家进入⭐优秀档 (VTR≥0.28)
  输出: /tmp/23companies_complete_vtr_ranking.csv
  状态: 排名完成

Step 7: 生成分析报告 ✅
  输出: /tmp/9companies_analysis_report.md
  内容:
    - 整体表现分析
    - 细分行业对比
    - 投资组合建议
    - 风险提示
  状态: 报告完整
```

---

## ⚠️ 常见错误及修正

### 错误1: 先提取σ_down，后确定细分行业

**错误流程**:
```
Step 1: 收集估值数据
Step 2: 提取σ_down数据 ❌ (不知道需要哪些ETF)
Step 3: 确定细分行业归属 ❌ (顺序颠倒)
```

**修正流程**:
```
Step 1: 收集估值数据
Step 2: 确定细分行业归属 ✅ (先知道需要哪些ETF)
Step 3: 提取σ_down数据 ✅ (针对性提取)
```

**原因**: 只有先确定细分行业归属，才知道需要提取哪些ETF的σ_down数据，避免盲目查找。

---

### 错误2: 多业务公司忽略利润权重

**错误示例**:
```python
紫金矿业:
  细分行业: 铜矿开采 ❌ (忽略黄金业务)
  σ_down: 23.02%
```

**修正示例**:
```python
紫金矿业:
  细分行业1: 铜矿开采 (60%利润)
  细分行业2: 黄金开采 (40%利润)
  加权σ_down: 0.6×23.02% + 0.4×13.06% = 19.04% ✅
```

---

### 错误3: 细分行业名称不一致

**错误示例**:
```yaml
公司映射表: "半导体材料-CMP抛光液"
σ_down数据表: "半导体材料" ❌ (名称不匹配)
```

**修正方法**:
```yaml
# 统一使用docs/PRECISE_INDUSTRY_SEGMENTATION_V7.md中的标准名称
公司映射表: "半导体材料-CMP"
σ_down数据表: "半导体材料-CMP" ✅
```

---

## 📊 完整输出清单 (更新版)

### Phase 0 输出

```
data/
├── company_financials.xlsx         # 财报数据
├── company_expected_returns.xlsx   # 期望收益
└── (可选) raw_financials/          # 原始财报PDF

docs/subindustry_outlook/
├── fabless_chip_design.md          # 芯片设计展望
├── semiconductor_equipment_backend.md  # 半导体设备展望
├── optical_module.md               # 光通信展望
├── ... (共13个细分行业)
```

### Phase 1 输出 (更新)

```
data/
├── company_subindustry_mapping.yml ⚠️ 新增: 公司-细分行业归属
├── subindustry_sigma_down.csv      # 细分行业风险
└── sigma_down_calculation_log.txt  # σ_down计算日志
```

### Phase 2 输出

```
data/
└── company_subindustry_vtr.csv     # VTR排名
```

### Phase 3 输出

```
data/
├── portfolio_allocation.xlsx       # 组合配置
├── trade_log.xlsx                 # 交易记录
└── (可选) backtest_results.xlsx   # 回测结果

docs/
└── (可选) backtest_report.md      # 回测报告
```

---

## 🔧 核心脚本更新

### 1. `scripts/calculate_subindustry_sigma_down.py`

**功能**: 计算细分行业ETF的σ_down

**输入**:
- 细分行业ETF映射表 (脚本内配置)
- Yahoo Finance历史数据

**输出**:
- `data/subindustry_sigma_down.csv`

**使用场景**:
- 首次执行时计算所有13个细分行业
- 新增行业时补充计算
- 每季度更新时重新计算

---

### 2. `scripts/build_company_subindustry_mapping.py`

**功能**: 建立公司-细分行业映射并计算VTR

**输入** (需手工配置):
- `SUBINDUSTRY_SIGMA_DOWN`: 细分行业σ_down (从Step 1.2提取)
- `COMPANY_SUBINDUSTRY_EXPOSURE`: 公司归属+期望收益 (从Step 1.1和Phase 0提取)

**输出**:
- `data/company_subindustry_vtr.csv`
- 控制台打印VTR排名

**关键修改** (配置前置条件):
```python
# 确保以下数据已准备好:
# 1. data/subindustry_sigma_down.csv (Step 1.2输出)
# 2. data/company_subindustry_mapping.yml (Step 1.1输出)
# 3. data/company_expected_returns.xlsx (Phase 0输出)
```

---

### 3. `scripts/fetch_valuation_data.py` (估值数据采集)

**功能**: Yahoo Finance API自动获取实时估值数据

**输入**:
- 公司Ticker列表

**输出**:
- `data/valuation_data.xlsx` (4张分析表)
- `data/valuation_data.yml` (YAML配置)

**使用场景**:
- 新增公司时优先使用
- 每季度更新时刷新估值

---

## ⏱️ 时间投入估算 (更新版)

### 首次执行 (8-12小时)

```
Phase 0: 信息收集 (4-7小时)
  ├─ Step 0.1: 财报数据收集 (1-2小时)
  ├─ Step 0.2: 行业分析 (2-3小时)
  └─ Step 0.3: 个股预期 (1-2小时)

Phase 1: 风险计算 (0.5-1小时) ⚠️ 新增Step 1.1增加时间
  ├─ Step 1.1: 确定细分行业归属 (0.3小时)
  └─ Step 1.2: 提取σ_down (0.2小时)

Phase 2: VTR计算 (0.5小时)

Phase 3: 投资决策 (2-8小时)
  ├─ Step 3.1: 组合生成 (1小时)
  ├─ Step 3.2: 回测验证 (可选,4-6小时)
  └─ Step 3.3: 交易执行 (1小时)

总计: 7-16.5小时 (不含回测: 7-10.5小时)
```

### 新增公司快速流程 (3-5小时)

```
Step 1: 收集估值数据 (0.25小时)
Step 2: 搜集财报和行业数据 (2-3小时)
Step 3: 确定细分行业归属 (0.5小时) ⚠️ 关键步骤
Step 4: 提取σ_down (0.25小时)
Step 5: 计算期望收益 (1-2小时)
Step 6: 计算VTR并排名 (0.25小时)
Step 7: 生成分析报告 (0.5小时)

总计: 4.75-6.75小时
```

---

## 📚 关键文档参考

### 方法论文档
- `docs/V7.3_SUBINDUSTRY_SIGMA_ANALYSIS.md` - 细分行业σ_down完整分析
- `docs/PRECISE_INDUSTRY_SEGMENTATION_V7.md` - **精确细分行业定义** (Step 1.1必读)
- `docs/SCENARIO_ANALYSIS_FRAMEWORK.md` - 场景分析框架

### 数据文档
- `docs/SECTOR_DOWNSIDE_RISK_DATA.md` - 行业σ_down数据表
- `docs/EBIT_RATE_ASSUMPTIONS.md` - 分部估值EBIT率假设

### 执行指南
- `EXECUTION_GUIDE_V7.3.md` - VTR计算阶段快速指南
- `COMPLETE_WORKFLOW_V7.3_UPDATED.md` - **本文档** (端到端完整流程)

---

## 🎯 核心原则再次强调

### 1. 执行顺序不可颠倒

```
❌ 错误: 先提取σ_down → 后确定细分行业
✅ 正确: 先确定细分行业 → 后提取σ_down
```

**原因**: 只有先知道细分行业归属，才知道需要提取哪些ETF数据。

---

### 2. VTR分母必须用纯σ_down

```python
# ✅ 正确:
VTR = 期望收益 / 细分行业σ_down

# ❌ 错误:
VTR = 期望收益 / Scheme C复合风险
VTR = 期望收益 / (σ_down + β + Frag)
```

---

### 3. 细分行业粒度与收益分析一致

```yaml
# ✅ 正确:
安集科技:
  收益分析粒度: "半导体材料-CMP" (CMP市占率10%)
  风险分母粒度: "半导体材料ETF" σ_down=21.76%

# ❌ 错误:
安集科技:
  收益分析粒度: "半导体材料-CMP"
  风险分母粒度: "半导体大行业" σ_down=24.14% (粒度不匹配)
```

---

### 4. 多业务公司必须加权

```python
# ✅ 正确:
紫金矿业 σ_down = 0.6×铜(23.02%) + 0.4×黄金(13.06%) = 19.04%

# ❌ 错误:
紫金矿业 σ_down = 铜(23.02%) (忽略黄金业务)
```

---

## 📞 问题反馈

如在执行过程中遇到问题:

1. **检查执行清单**: 每个Step都有详细清单,逐项核对
2. **查看错误修正**: 参考本文档"常见错误及修正"章节
3. **GitHub提Issue**: https://github.com/LpcPaul/downrisk-get/issues

**Issue模板**:
```markdown
**执行阶段**: Phase X / Step X.X
**问题描述**: [具体错误信息或疑惑]
**已尝试方案**: [列出已尝试的解决方法]
**环境信息**: Python版本/操作系统/依赖库版本
```

---

**文档版本**: V7.3 Complete Workflow (Updated)
**创建日期**: 2025-10-07
**最后更新**: 2025-10-08
**更新内容**: 修正新增公司流程顺序，新增Step 1.1确定细分行业归属
**维护者**: @LpcPaul
