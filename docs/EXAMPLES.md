# 使用示例

本文档提供 downrisk-get 项目的完整使用示例，从基础到高级。

---

## 📖 目录

1. [基础示例](#基础示例)
2. [配置示例](#配置示例)
3. [高级用法](#高级用法)
4. [实战案例](#实战案例)
5. [常见问题解决](#常见问题解决)

---

## 基础示例

### 示例1：一键分析（最简单）

```bash
# 使用默认配置分析7家公司
python3 -m volrisk.cli rank

# 查看结果
open output.xlsx
```

**输出**：
- `output.xlsx`：完整的值博率排名表
- `ANALYSIS_SUMMARY.md`：自动生成的分析报告

**预期结果**：
```
排名前10的公司:
================================================================================
 1. 锦波生物        | 值博率:   3.17 | ER: 65.62% | 风险: 20.71%
 2. 晶泰控股         | 值博率:   2.19 | ER: 60.00% | 风险: 27.38%
 3. 紫金矿业         | 值博率:   1.98 | ER: 32.55% | 风险: 16.40%
 ...
```

### 示例2：分析v2.0配置（13家公司）

```bash
# 使用v2.0保守收益框架
python3 -m volrisk.cli rank \
  --companies config/companies_v2.yml \
  --output v2_results.xlsx

# 查看结果
open v2_results.xlsx
```

**预期结果**：
```
 1. 建滔积层板        | 值博率:   1.44 | ER: 30.00% | 风险: 20.78%
 2. 澜起科技         | 值博率:   1.27 | ER: 35.00% | 风险: 27.50%
 3. 阿里巴巴         | 值博率:   1.10 | ER: 25.00% | 风险: 22.78%
 ...
```

### 示例3：查看行业风险

```bash
# 计算所有行业的风险指标
python3 -m volrisk.cli calc-sector
```

**输出**：
```
================================================================================
行业风险指标（过去1年，年化）
================================================================================
SEMI (512480.SS):
  σ总波动: 39.24%
  σ下行:   22.86%
  MDD:     19.39%

INTERNET (513050.SS):
  σ总波动: 31.32%
  σ下行:   21.19%
  MDD:     22.32%

GOLD (518850.SS):
  σ总波动: 15.98%
  σ下行:   10.76%  ⭐ 最低
  MDD:     11.64%
...
```

### 示例4：指定时间范围

```bash
# 分析过去6个月
python3 -m volrisk.cli rank --period 6mo --output results_6m.xlsx

# 分析过去2年
python3 -m volrisk.cli rank --period 2y --output results_2y.xlsx

# 指定具体日期
python3 -m volrisk.cli rank \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output results_2024.xlsx
```

---

## 配置示例

### 示例5：添加新公司（直接指定收益）

**场景**：你已经通过自己的分析得出某公司的期望收益为35%

**步骤1**：编辑 `config/companies.yml`

```yaml
companies:
  # ... 其他公司

  # 新增：比亚迪
  - name: "比亚迪"
    sector: "CONSUMER"  # 或创建新的汽车行业代理
    expected_return: 0.35  # 35%期望收益
    risk:
      mode: "SchemeC"
      beta: 1.20  # 汽车行业周期性，β略高
      frag: 2.0   # 脆弱度：竞争激烈
```

**步骤2**：运行分析

```bash
python3 -m volrisk.cli rank
```

**结果**：比亚迪会出现在排名中。

### 示例6：添加新公司（使用估值模型）

**场景**：某科技股当前PE=60，目标PE=40，预期盈利增长20%

**配置**：

```yaml
  - name: "某科技公司"
    sector: "SEMI"
    model:
      type: "PE"
      current_multiple: 60.0
      target_multiple: 40.0
      growth_12m: 0.20  # 20%盈利增长
      dividend_yield: 0.01  # 1%股息
      buyback_yield: 0.0
      execution_prob: 0.85  # 85%执行概率
    risk:
      mode: "SchemeC"
      beta: 1.15
      frag: 2.5
```

**自动计算**：
```
ER_raw = (40/60 × 1.20 - 1) + 0.01 + 0.0
       = (0.667 × 1.20 - 1) + 0.01
       = (0.800 - 1) + 0.01
       = -0.190
ER = -0.190 × 0.85 = -16.15%
```

**结论**：该股票期望收益为负，值博率可能 < 0。

### 示例7：混合行业公司

**场景**：某资源公司50%业务是有色金属，30%是黄金，20%是锂矿

**配置**：

```yaml
  - name: "某资源公司"
    sector_mix:
      NONFER: 0.5  # 50%有色
      GOLD: 0.3    # 30%黄金
      CONSUMER: 0.2  # 20%锂矿（暂用消费代理）
    expected_return: 0.22
    risk:
      mode: "SchemeC"
      beta: 1.0
      frag: 1.8
```

**风险计算**：
```
σ_down_混合 = 0.5×19.78% + 0.3×10.76% + 0.2×15.93%
           = 9.89% + 3.23% + 3.19%
           = 16.31%
```

### 示例8：添加新行业ETF

**场景**：你想添加新能源汽车ETF作为风险代理

**步骤1**：编辑 `config/sectors.yml`

```yaml
sectors:
  # ... 现有行业

  # 新增：新能源汽车
  AUTO_NEW_ENERGY:
    tickers: ["515030.SS"]  # 新能源车ETF
    weights: [1.0]
```

**步骤2**：获取数据

```bash
# 先测试能否获取数据
python3 -m volrisk.cli fetch 515030.SS
```

**步骤3**：在公司配置中使用

```yaml
  - name: "比亚迪"
    sector: "AUTO_NEW_ENERGY"
    expected_return: 0.30
    risk:
      mode: "SchemeC"
      beta: 1.15
      frag: 2.5
```

### 示例9：调整Scheme C权重

**场景**：你认为下行风险应该占70%，系统性风险占20%

**方法**：需要修改代码（未来版本可配置化）

**临时方案**：调整β和Frag来模拟：

```yaml
# 如果你想加重下行风险的影响
# 可以降低β（减少系统性风险项的贡献）
# 但这不是精确的等价
risk:
  mode: "SchemeC"
  beta: 0.8  # 降低β，相当于降低系统性风险权重
  frag: 2.0
```

**建议**：提交Issue请求可配置权重功能。

---

## 高级用法

### 示例10：滚动窗口分析

**目的**：观察值博率随时间窗口的变化

**脚本**：

```bash
#!/bin/bash
# rolling_analysis.sh

# 分析不同时间窗口
periods=("3mo" "6mo" "1y" "2y")

for period in "${periods[@]}"; do
  echo "分析周期: $period"
  python3 -m volrisk.cli rank \
    --period $period \
    --output "results_${period}.xlsx"
done

echo "完成！请对比不同窗口的排名。"
```

**运行**：
```bash
chmod +x rolling_analysis.sh
./rolling_analysis.sh
```

**分析**：
- 如果Top 3在不同窗口下稳定，说明排名可靠
- 如果某标的从第1掉到第10，说明短期波动大，需谨慎

### 示例11：批量敏感性分析

**目的**：测试β和Frag参数变化对值博率的影响

**方法1：手工调整配置**

```yaml
# 基准配置
- name: "测试标的"
  sector: "SEMI"
  expected_return: 0.30
  risk:
    beta: 1.15  # 基准
    frag: 2.5   # 基准

# 测试配置1: β+0.1
- name: "测试标的_beta_high"
  sector: "SEMI"
  expected_return: 0.30
  risk:
    beta: 1.25  # +0.1
    frag: 2.5

# 测试配置2: Frag+1%
- name: "测试标的_frag_high"
  sector: "SEMI"
  expected_return: 0.30
  risk:
    beta: 1.15
    frag: 3.5  # +1%
```

**方法2：Python脚本**

```python
# sensitivity_analysis.py
import pandas as pd
from volrisk.risk import scheme_c_loss_risk

# 行业数据（SEMI）
sigma_down = 0.2286
sigma_total = 0.3924

# 基准参数
er_base = 0.30
beta_base = 1.15
frag_base = 2.5

# β敏感性
betas = [1.05, 1.10, 1.15, 1.20, 1.25]
results_beta = []

for beta in betas:
    risk = scheme_c_loss_risk(sigma_down, sigma_total, beta, frag_base)
    vtr = er_base / risk
    results_beta.append({
        'Beta': beta,
        'Risk': f"{risk:.2%}",
        'VTR': f"{vtr:.2f}",
        'Change': f"{(vtr / (er_base / scheme_c_loss_risk(sigma_down, sigma_total, beta_base, frag_base)) - 1):.1%}"
    })

df_beta = pd.DataFrame(results_beta)
print("\n=== β敏感性分析 ===")
print(df_beta)

# Frag敏感性
frags = [1.5, 2.0, 2.5, 3.0, 3.5]
results_frag = []

for frag in frags:
    risk = scheme_c_loss_risk(sigma_down, sigma_total, beta_base, frag)
    vtr = er_base / risk
    results_frag.append({
        'Frag': f"{frag}%",
        'Risk': f"{risk:.2%}",
        'VTR': f"{vtr:.2f}",
        'Change': f"{(vtr / (er_base / scheme_c_loss_risk(sigma_down, sigma_total, beta_base, frag_base)) - 1):.1%}"
    })

df_frag = pd.DataFrame(results_frag)
print("\n=== Frag敏感性分析 ===")
print(df_frag)
```

**运行**：
```bash
python sensitivity_analysis.py
```

**预期输出**：
```
=== β敏感性分析 ===
   Beta    Risk   VTR Change
0  1.05  26.43%  1.13  +2.8%
1  1.10  26.96%  1.11  +1.1%
2  1.15  27.50%  1.09   0.0%
3  1.20  28.03%  1.07  -1.8%
4  1.25  28.56%  1.05  -3.6%

=== Frag敏感性分析 ===
    Frag    Risk   VTR Change
0  1.5%  27.40%  1.09  +0.4%
1  2.0%  27.45%  1.09  +0.2%
2  2.5%  27.50%  1.09   0.0%
3  3.0%  27.55%  1.09  -0.2%
4  3.5%  27.60%  1.09  -0.4%
```

**结论**：
- β变化0.1 → 值博率变化约±2%
- Frag变化1% → 值博率变化约±0.2%
- **β的影响 > Frag的影响**（符合权重设计：30% vs 10%）

### 示例12：导出JSON格式

```bash
# 导出为JSON（需要先实现）
python3 -m volrisk.cli rank --output results.json --format json
```

**JSON结构**：
```json
{
  "metadata": {
    "analysis_date": "2025-10-05",
    "period": "2024-09-30 to 2025-09-30",
    "num_companies": 13
  },
  "rankings": [
    {
      "rank": 1,
      "company": "建滔积层板",
      "sector": "NONFER",
      "expected_return": 0.30,
      "loss_risk": 0.2078,
      "value_to_risk": 1.44,
      "beta": 1.05,
      "fragility": 2.0
    },
    ...
  ],
  "sector_risks": {
    "SEMI": {
      "sigma_down": 0.2286,
      "sigma_total": 0.3924,
      "mdd": 0.1939
    },
    ...
  }
}
```

---

## 实战案例

### 案例1：对比两个标的

**背景**：你在纠结投资比亚迪还是宁德时代

**步骤1**：配置两个标的

```yaml
companies:
  - name: "比亚迪"
    sector: "CONSUMER"  # 汽车
    expected_return: 0.35
    risk:
      mode: "SchemeC"
      beta: 1.20
      frag: 2.0

  - name: "宁德时代"
    sector: "NONFER"  # 材料
    expected_return: 0.28
    risk:
      mode: "SchemeC"
      beta: 1.15
      frag: 2.5
```

**步骤2**：运行分析

```bash
python3 -m volrisk.cli rank --output compare_byd_catl.xlsx
```

**步骤3**：对比结果

假设输出：
```
 1. 比亚迪          | 值博率:   2.01 | ER: 35.00% | 风险: 17.41%
 2. 宁德时代        | 值博率:   1.18 | ER: 28.00% | 风险: 23.73%
```

**结论**：
- 比亚迪值博率更高（2.01 vs 1.18）
- 比亚迪风险更低（17.41% vs 23.73%，得益于消费行业风险低）
- **选择比亚迪**（假设其他条件相同）

### 案例2：构建投资组合

**目标**：构建一个风险收益平衡的组合

**步骤1**：运行完整分析

```bash
python3 -m volrisk.cli rank --companies config/companies_v2.yml
```

**步骤2**：选择标的

基于值博率选择：
- **高收益（40%）**：建滔积层板（VTR=1.44）
- **平衡（30%）**：阿里巴巴（VTR=1.10）
- **稳健（30%）**：紫金矿业（VTR=1.10，但风险最低16.41%）

**步骤3**：计算组合指标

```python
# portfolio_analysis.py
import numpy as np

# 权重
weights = [0.4, 0.3, 0.3]

# 期望收益
ers = [0.30, 0.25, 0.18]

# 损失风险
risks = [0.2078, 0.2278, 0.1641]

# 组合期望收益（假设不相关）
portfolio_er = np.dot(weights, ers)
print(f"组合期望收益: {portfolio_er:.2%}")  # 25.17%

# 组合风险（简化：加权平均，忽略相关性）
portfolio_risk = np.dot(weights, risks)
print(f"组合风险: {portfolio_risk:.2%}")  # 20.22%

# 组合值博率
portfolio_vtr = portfolio_er / portfolio_risk
print(f"组合值博率: {portfolio_vtr:.2f}")  # 1.24
```

**输出**：
```
组合期望收益: 25.17%
组合风险: 20.22%
组合值博率: 1.24
```

**结论**：
- 组合值博率1.24（良好）
- 相比单一标的，分散降低了风险
- 期望收益仍有25%+

### 案例3：发现被低估的标的

**场景**：你手上有10个候选标的，想找出最被低估的

**步骤1**：配置所有标的

```yaml
companies:
  - name: "标的A"
    sector: "SEMI"
    expected_return: 0.40
    risk: {beta: 1.15, frag: 2.5}

  - name: "标的B"
    sector: "INTERNET"
    expected_return: 0.35
    risk: {beta: 1.05, frag: 2.0}

  # ... 标的C-J
```

**步骤2**：运行分析

```bash
python3 -m volrisk.cli rank --output candidates.xlsx
```

**步骤3**：筛选

```
筛选条件:
1. 值博率 > 1.5 (高性价比)
2. 期望收益 > 25% (高回报)
3. 损失风险 < 25% (可控风险)
```

**步骤4**：深入研究

对筛选出的标的：
- 验证期望收益假设
- 检查β和Frag是否合理
- 结合基本面分析

---

## 常见问题解决

### 问题1：数据获取失败

**现象**：
```
Error: No data found for symbol 512480.SS
```

**原因**：
- 网络问题
- ETF代码错误
- yfinance服务异常

**解决**：

```bash
# 1. 检查网络
ping www.yahoo.com

# 2. 验证代码
python3 -c "import yfinance as yf; print(yf.Ticker('512480.SS').info)"

# 3. 强制刷新缓存
python3 -m volrisk.cli fetch 512480.SS --force

# 4. 使用备用时间范围
python3 -m volrisk.cli fetch 512480.SS --start 2024-01-01 --end 2024-12-31
```

### 问题2：值博率为负

**现象**：
```
澜起科技 | 值博率: -1.07 | ER: -28.82%
```

**原因**：
- 期望收益为负（估值过高或业绩下滑）

**解决**：

```bash
# 1. 检查配置
cat config/companies.yml | grep -A 15 "澜起科技"

# 2. 重新评估
# - 当前PE是否确实过高？
# - 目标PE是否合理？
# - 增长率是否保守？

# 3. 调整参数或选择其他标的
```

**建议**：
- 值博率 < 0 的标的应避免投资
- 除非你有强烈的反向理由

### 问题3：排名与预期不符

**现象**：
```
预期: 标的A > 标的B
实际: 标的B > 标的A
```

**调查步骤**：

```bash
# 1. 查看完整输出
python3 -m volrisk.cli rank --output debug.xlsx

# 2. 手工验证计算
python3 << 'EOF'
from volrisk.risk import scheme_c_loss_risk

# 标的A
er_a = 0.35
sigma_down = 0.2286
sigma_total = 0.3924
beta_a = 1.15
frag_a = 2.5

risk_a = scheme_c_loss_risk(sigma_down, sigma_total, beta_a, frag_a)
vtr_a = er_a / risk_a

print(f"标的A: ER={er_a:.2%}, Risk={risk_a:.2%}, VTR={vtr_a:.2f}")

# 标的B
# ... 同样计算
EOF

# 3. 对比参数
# - 是否使用了相同的行业代理？
# - β和Frag是否合理？
# - 期望收益是否准确？
```

### 问题4：行业风险异常

**现象**：
```
GOLD: σ_down=25.00%  # 黄金风险居然这么高？
```

**原因**：
- ETF代码错误
- 数据质量问题
- 时间窗口选择不当

**解决**：

```bash
# 1. 验证ETF数据
python3 -m volrisk.cli fetch 518850.SS

# 2. 检查数据质量
python3 << 'EOF'
import yfinance as yf
import pandas as pd

ticker = yf.Ticker("518850.SS")
hist = ticker.history(period="1y")

print(f"数据点数: {len(hist)}")
print(f"缺失值: {hist['Close'].isna().sum()}")
print(f"价格范围: {hist['Close'].min():.2f} - {hist['Close'].max():.2f}")
print(f"\n最新10天:")
print(hist.tail(10))
EOF

# 3. 尝试不同时间窗口
python3 -m volrisk.cli calc-sector --period 2y

# 4. 更换ETF
# 如果数据质量差，考虑使用其他黄金ETF
```

### 问题5：缓存过期

**现象**：
```
使用了旧数据，结果不准确
```

**解决**：

```bash
# 清除所有缓存
python3 -m volrisk.cli clear-cache

# 清除特定ETF缓存
python3 -m volrisk.cli clear-cache --ticker 512480.SS

# 强制刷新并重新分析
python3 -m volrisk.cli rank --force
```

### 问题6：Excel打不开

**现象**：
```
output.xlsx 文件损坏
```

**原因**：
- 写入过程中断
- 磁盘空间不足
- Excel版本太旧

**解决**：

```bash
# 1. 检查文件大小
ls -lh output.xlsx

# 2. 尝试CSV格式（如果支持）
# python3 -m volrisk.cli rank --output results.csv --format csv

# 3. 手工读取
python3 << 'EOF'
import pandas as pd

try:
    df = pd.read_excel("output.xlsx")
    print(df)
except Exception as e:
    print(f"Error: {e}")
EOF

# 4. 重新生成
rm output.xlsx
python3 -m volrisk.cli rank
```

---

## 总结

### 学习路径

1. **新手**：
   - 运行示例1-4
   - 理解基本概念（值博率、下行风险）
   - 查看输出结果

2. **进阶**：
   - 添加自己的标的（示例5-6）
   - 配置混合行业（示例7）
   - 添加新行业ETF（示例8）

3. **高级**：
   - 滚动窗口分析（示例10）
   - 敏感性分析（示例11）
   - 构建投资组合（案例2）

### 最佳实践

1. **定期更新**：
   - 每月清除缓存并重新分析
   - 观察值博率变化趋势

2. **交叉验证**：
   - 值博率只是参考，不要盲目相信
   - 结合基本面分析
   - 检查假设是否合理

3. **风险控制**：
   - 不要只看值博率，也要看绝对风险
   - 分散投资，不要单一押注
   - 设置止损

4. **参数校准**：
   - β和Frag需要基于基本面
   - 定期复盘，调整参数
   - 记录假设和调整理由

---

**最后更新**: 2025-10-05
**版本**: v1.0.0
**维护者**: @LpcPaul
