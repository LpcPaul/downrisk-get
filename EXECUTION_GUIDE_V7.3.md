# V7.3 执行指南

**目标**: 确保后续执行项目的人严格按照V7.3策略输出结果

---

## ⚠️ 核心原则 (必须遵守)

### 1. VTR分母使用纯σ_down (禁止叠加)

```python
# ✅ 正确方法:
VTR = 期望收益(1年) / 细分行业σ_down

# ❌ 错误方法 (禁止):
VTR = 期望收益 / Scheme C复合风险  # ❌
VTR = 期望收益 / (σ_down + β + Frag)  # ❌
VTR = 期望收益 / (σ_down + β×σ_total + MDD)  # ❌
```

**Scheme C的正确用途**:
```
Scheme C = 0.6×σ_down + 0.3×(β×σ_total) + 0.1×Frag

✅ 用于: 综合风险评估,投资组合风险管理
❌ 禁止: 用作VTR分母
```

### 2. 细分行业粒度与收益分析一致

```yaml
# ✅ 正确示例:
光迅科技:
  收益分析行业: "光通信模块" (800G/1.6T技术迭代期)
  风险分母: 光通信ETF (516630.SS) σ_down = 25.43%
  匹配度: ✅ 完全一致

# ❌ 错误示例:
光迅科技:
  收益分析行业: "光通信模块"
  风险分母: TMT大行业 σ_down = 23.76%
  匹配度: ❌ 粒度不匹配
```

### 3. 多业务公司必须加权

```python
# ✅ 正确:
紫金矿业:
  铜矿开采 (60%利润): σ_down = 23.02%
  黄金开采 (40%利润): σ_down = 13.06%
  加权σ_down = 0.6 × 23.02% + 0.4 × 13.06% = 19.04%

# ❌ 错误:
紫金矿业:
  仅用铜矿: σ_down = 23.02%  # 忽略黄金业务
  仅用黄金: σ_down = 13.06%  # 忽略铜矿业务
```

### 4. 时间窗口统一1年

```yaml
收益窗口: 1年
风险窗口: 1年  # 必须与收益窗口一致
ETF数据窗口: 2024-10-06至2025-10-06 (1年)
```

---

## 📋 V7.3标准执行流程

### Step 1: 计算细分行业σ_down

```bash
python3 scripts/calculate_subindustry_sigma_down.py
```

**输出检查**:
- ✅ 文件生成: `data/subindustry_sigma_down.csv`
- ✅ 13个细分行业全部有数据
- ✅ σ_down在10%-30%合理区间内

**关键数据**:
```
细分行业              ETF代码       σ_down
Fabless芯片设计      512760.SS    23.75%
半导体设备-后道封装   516290.SS    21.66%
半导体材料           516020.SS    21.76%
光通信模块           516630.SS    25.43%
通信设备-海缆光纤     515880.SS    26.98%
PC制造              512720.SS    23.76%
CCL覆铜板           159870.SZ    22.79%
磷化工-LFP          159870.SZ    22.79%
黄金开采            518850.SS    13.06%
铜矿开采            562800.SS    23.02%
输变电设备          159611.SZ    13.13%
多晶硅              516290.SS    21.66%
```

### Step 2: 建立公司-细分行业映射

```bash
python3 scripts/build_company_subindustry_mapping.py
```

**配置检查** (`scripts/build_company_subindustry_mapping.py`):

```python
# ✅ 必须检查的配置项:
COMPANY_SUBINDUSTRY_EXPOSURE = {
    '澜起科技': {
        'exposures': [('Fabless芯片设计', 1.0)],  # ✅ 单业务
        'expected_return_1y': 0.045,
    },

    '紫金矿业': {
        'exposures': [
            ('铜矿开采', 0.60),  # ✅ 多业务加权
            ('黄金开采', 0.40),
        ],
        'expected_return_1y': -0.240,
    },

    '特变电工': {
        'exposures': [
            ('输变电设备', 0.60),  # ⚠️ 注意不是SEMI+CHEM!
            ('多晶硅', 0.40),
        ],
        'expected_return_1y': -0.068,
    },
}
```

**输出检查**:
- ✅ 文件生成: `data/company_subindustry_vtr.csv`
- ✅ 14家公司全部有VTR数据
- ✅ VTR Top5: ASMPT(0.68) > 川恒(0.57) > 建滔(0.38) > 光迅(0.34) > 中天(0.28)

### Step 3: 验证VTR计算

**手工验证案例: ASMPT**

```
输入数据:
  期望收益(1年) = 14.7%
  细分行业: 半导体设备-后道封装
  σ_down = 21.66% (从516290.SS实测)

VTR计算:
  VTR = 14.7% / 21.66%
      = 0.6787
      ≈ 0.68 ✅

预期输出:
  ASMPT排名第1,VTR=0.68,评级⭐优秀
```

**手工验证案例: 紫金矿业**

```
输入数据:
  期望收益(1年) = -24.0%
  细分行业暴露:
    铜矿开采 (60%): σ_down = 23.02%
    黄金开采 (40%): σ_down = 13.06%

加权σ_down计算:
  σ_down = 0.6 × 23.02% + 0.4 × 13.06%
         = 13.81% + 5.22%
         = 19.04% ✅

VTR计算:
  VTR = -24.0% / 19.04%
      = -1.26 ✅

预期输出:
  紫金矿业排名第13,VTR=-1.26,评级⚠️不佳
```

### Step 4: 生成投资组合

**V7.3推荐配置**:

| 层级 | 标的 | 权重 | VTR | σ_down | 配置逻辑 |
|------|------|------|-----|--------|---------|
| 进攻层 | ASMPT | 30% | 0.68 | 21.66% | 周期拐点,高VTR,风险更低 |
| 底仓层 | 川恒股份 | 30% | 0.57 | 22.79% | 稳健成长,真实低估 |
| 均衡层 | 建滔积层板 | 20% | 0.38 | 22.79% | AI受益,VTR优秀 |
| 均衡层 | 光迅科技 | 12% | 0.34 | 25.43% | 800G放量,风险略高 |
| 试探仓 | 中天科技 | 5% | 0.28 | 26.98% | 海缆催化,小仓位,风险踩线 |
| 现金 | - | 3% | - | - | 灵活调仓 |

**组合指标验证**:
```
加权期望收益 = 30%×14.7% + 30%×12.9% + 20%×8.6% + 12%×8.7% + 5%×7.6%
            = 4.41% + 3.87% + 1.72% + 1.04% + 0.38%
            = 11.42% ✅ (目标11-12%)

加权σ_down = 30%×21.66% + 30%×22.79% + 20%×22.79% + 12%×25.43% + 5%×26.98%
           = 6.50% + 6.84% + 4.56% + 3.05% + 1.35%
           = 22.30%

组合VTR = 11.42% / 22.30% = 0.51 ✅ (优秀,超过阈值0.28)
```

---

## 🔧 常见错误及修正

### 错误1: 使用Scheme C作为VTR分母

**错误代码**:
```python
# ❌ 错误:
scheme_c_risk = 0.6*sigma_down + 0.3*(beta*sigma_total) + 0.1*frag
vtr = expected_return / scheme_c_risk
```

**修正代码**:
```python
# ✅ 正确:
vtr = expected_return / sigma_down  # 纯σ_down
```

### 错误2: 使用大行业ETF

**错误配置**:
```python
# ❌ 错误:
光迅科技:
  sector = 'TMT'  # 大行业
  sigma_down = SECTOR_SIGMA_DOWN['TMT']  # 23.76%
```

**修正配置**:
```python
# ✅ 正确:
光迅科技:
  subindustry = '光通信模块'  # 细分行业
  sigma_down = SUBINDUSTRY_SIGMA_DOWN['光通信模块']  # 25.43%
```

### 错误3: 多业务公司未加权

**错误计算**:
```python
# ❌ 错误:
紫金矿业:
  sigma_down = SUBINDUSTRY_SIGMA_DOWN['铜矿开采']  # 仅用铜,忽略黄金
```

**修正计算**:
```python
# ✅ 正确:
紫金矿业:
  sigma_down = 0.6 * SUBINDUSTRY_SIGMA_DOWN['铜矿开采'] + \
               0.4 * SUBINDUSTRY_SIGMA_DOWN['黄金开采']
  # = 0.6 × 23.02% + 0.4 × 13.06% = 19.04%
```

### 错误4: 时间窗口不一致

**错误设置**:
```python
# ❌ 错误:
expected_return = calculate_return(period='2y')  # 2年收益
sigma_down = calculate_sigma(period='1y')  # 1年风险
vtr = expected_return / sigma_down  # 不可比!
```

**修正设置**:
```python
# ✅ 正确:
expected_return = calculate_return(period='1y')  # 1年收益
sigma_down = calculate_sigma(period='1y')  # 1年风险
vtr = expected_return / sigma_down  # 可比
```

### 错误5: 特变电工行业分类错误

**错误配置** (V7.2的错误):
```python
# ❌ 错误:
特变电工:
  exposures = [
    ('SEMI', 0.5),   # 与业务无关!
    ('CHEM', 0.5),   # 与业务无关!
  ]
```

**修正配置** (V7.3):
```python
# ✅ 正确:
特变电工:
  exposures = [
    ('输变电设备', 0.6),  # 变压器+线缆
    ('多晶硅', 0.4),     # 光伏材料
  ]
```

---

## 📊 输出检查清单

### 必须检查的输出

- [ ] **VTR Top5排名**:
  1. ASMPT (0.68)
  2. 川恒股份 (0.57)
  3. 建滔积层板 (0.38)
  4. 光迅科技 (0.34)
  5. 中天科技 (0.28)

- [ ] **VTR阈值** (基于当期样本):
  - ⭐优秀 (Top30%): VTR ≥ 0.28
  - ✓平衡 (30-70%): -0.16 ≤ VTR < 0.28
  - ⚠️不佳 (Bottom30%): VTR < -0.16

- [ ] **细分行业σ_down合理性**:
  - 半导体: 21.66%-23.75% ✅
  - TMT: 23.76%-26.98% ✅
  - 化工: 22.79% ✅
  - 黄金: 13.06% ✅
  - 铜: 23.02% ✅
  - 输变电: 13.13% ✅

- [ ] **关键标的σ_down对比V7.2**:
  - ASMPT: 24.14%→21.66% (降低10.3%) ✅
  - 光迅: 23.76%→25.43% (提高7.0%) ✅
  - 中天: 23.76%→26.98% (提高13.5%) ✅
  - 特变: 23.46%→16.54% (降低29.5%) ✅

### 数据质量检查

```python
# 检查σ_down范围
for subindustry, data in SUBINDUSTRY_SIGMA_DOWN.items():
    sigma = data['sigma_down']
    assert 0.10 < sigma < 0.50, f"{subindustry} σ_down异常: {sigma}"

# 检查多业务公司权重之和
for company, data in COMPANY_SUBINDUSTRY_EXPOSURE.items():
    total_weight = sum([w for _, w in data['exposures']])
    assert abs(total_weight - 1.0) < 0.01, f"{company} 权重之和≠1: {total_weight}"

# 检查VTR计算
for company in companies:
    calculated_vtr = expected_return / sigma_down
    assert abs(calculated_vtr - output_vtr) < 0.01, f"{company} VTR计算错误"
```

---

## 📁 关键文件位置

### 核心脚本

```
scripts/
├── calculate_subindustry_sigma_down.py  # Step 1: 计算细分行业σ_down
└── build_company_subindustry_mapping.py # Step 2: 公司映射+VTR计算
```

### 配置文件

```
细分行业ETF配置 (硬编码在脚本中):
  SUBINDUSTRY_ETFS = {
    'Fabless芯片设计': {'etf_code': '512760.SS', ...},
    '光通信模块': {'etf_code': '516630.SS', ...},
    ...
  }

公司暴露配置 (硬编码在脚本中):
  COMPANY_SUBINDUSTRY_EXPOSURE = {
    '澜起科技': {'exposures': [('Fabless芯片设计', 1.0)], ...},
    '紫金矿业': {'exposures': [('铜矿开采', 0.6), ('黄金开采', 0.4)], ...},
    ...
  }
```

### 输出文件

```
data/
├── subindustry_sigma_down.csv      # 细分行业σ_down数据
└── company_subindustry_vtr.csv     # 公司VTR对比
```

### 文档

```
docs/
├── V7.3_SUBINDUSTRY_SIGMA_ANALYSIS.md  # V7.3完整分析
├── PRECISE_INDUSTRY_SEGMENTATION_V7.md # 细分行业定义
├── SCENARIO_ANALYSIS_FRAMEWORK.md      # 场景分析框架
└── EBIT_RATE_ASSUMPTIONS.md            # EBIT率假设文档
```

---

## 🔄 版本差异对照

### V7.3 vs V7.2 vs V7.1

| 维度 | V7.1 | V7.2 | V7.3 |
|------|------|------|------|
| **VTR分母** | Scheme C复合 ❌ | 纯σ_down ✅ | 纯σ_down ✅ |
| **行业粒度** | 大行业(5个) | 大行业(5个) ❌ | 细分行业(13个) ✅ |
| **收益计算** | 主观中性估计 ❌ | 主观中性估计 ❌ | 场景加权 ✅ |
| **VTR阈值** | 固定0.5 ❌ | 固定0.32 ❌ | 分位数0.28 ✅ |
| **时间窗口** | 2年→年化 ❌ | 1年 ✅ | 1年 ✅ |

### 关键标的VTR变化轨迹

```
ASMPT:
  V7.1: - (未追踪)
  V7.2: 0.61 (大行业SEMI σ_down=24.14%)
  V7.3: 0.68 (细分行业半导体设备 σ_down=21.66%) ✅

光迅科技:
  V7.1: - (未追踪)
  V7.2: 0.37 (大行业TMT σ_down=23.76%)
  V7.3: 0.34 (细分行业光通信 σ_down=25.43%) ✅

特变电工:
  V7.1: - (未追踪)
  V7.2: -0.29 (错误用SEMI+CHEM σ_down=23.46%) ❌
  V7.3: -0.41 (正确用输变电+多晶硅 σ_down=16.54%) ✅
```

---

## ⚠️ 关键提示

### 必须遵守的原则

1. **VTR分母=纯σ_down** (禁止叠加任何其他成分)
2. **细分行业粒度与收益分析一致** (不能用大行业替代细分)
3. **多业务公司必须加权** (按利润权重,不能只用单一业务)
4. **时间窗口统一1年** (收益和风险必须同尺度)
5. **VTR阈值用分位数** (不能用固定值,需根据样本计算)

### 数据更新频率

```
细分行业σ_down: 每季度更新 (重新运行Step 1)
公司期望收益: 每季度更新 (财报季后调整)
VTR排名: 每季度更新 (Step 2重新计算)
投资组合: 每季度调整 (根据新VTR排名)
```

### 异常情况处理

**情况1: 细分行业ETF数据缺失**
```
问题: 某细分ETF历史数据<50天
解决:
  优先级1: 寻找同类细分ETF替代
  优先级2: 使用大行业ETF (标注"暂无细分")
  优先级3: 用成分股加权计算
```

**情况2: 多业务公司利润权重难以确定**
```
问题: 公司未披露分部利润
解决:
  1. 用分部收入×EBIT率估算
  2. 参考同行对标公司EBIT率
  3. 标注"基于估算,存在±20%误差"
```

**情况3: VTR计算结果与预期差异过大**
```
问题: 重算后VTR与V7.2差异>50%
检查:
  1. σ_down是否用对细分行业ETF?
  2. 多业务公司是否正确加权?
  3. 期望收益是否用1年窗口?
  4. 是否误用了Scheme C复合风险?
```

---

## 📞 问题反馈

如发现执行过程中的问题,请在GitHub提Issue:
https://github.com/LpcPaul/downrisk-get/issues

**必需信息**:
- 执行的步骤 (Step 1/2/3/4)
- 错误信息或异常输出
- 使用的脚本版本
- Python环境 (python3 --version)

---

**文档版本**: V7.3
**最后更新**: 2025-10-06
**维护者**: @LpcPaul
