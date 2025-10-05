# 🚀 快速上手指南

## 5分钟完成值博率分析

### 步骤1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2: 运行分析

```bash
python3 -m volrisk.cli rank
```

就这么简单！系统会自动：
1. 获取7个行业ETF的历史数据（过去1年）
2. 计算每个行业的下行风险
3. 计算每家公司的值博率
4. 生成Excel报告 `output.xlsx`

### 步骤3: 查看结果

打开生成的 `output.xlsx` 文件，你将看到：
- 📊 完整的值博率排名
- 📉 行业风险指标
- 📈 期望收益分解
- 🎯 风险组成部分

---

## 📝 自定义分析

### 修改公司配置

编辑 `config/companies.yml`：

```yaml
companies:
  - name: "你的公司"
    sector: "SEMI"  # 选择行业
    expected_return: 0.50  # 50%期望收益
    risk:
      mode: "SchemeC"
      beta: 1.2  # β系数
      frag: 2.0  # 脆弱度(%)
```

### 添加新行业

编辑 `config/sectors.yml`：

```yaml
sectors:
  NEW_SECTOR:
    tickers: ["159915.SZ"]  # 创业板ETF
    weights: [1.0]
```

### 调整时间窗口

```bash
# 分析过去2年
python3 -m volrisk.cli rank --period 2y

# 指定具体日期
python3 -m volrisk.cli rank --start 2024-01-01 --end 2024-12-31
```

---

## 🔍 理解关键指标

### 值博率 (Value-to-Risk Ratio)
```
值博率 = 期望收益 ÷ 损失风险
```
- **> 2.0**: 优秀（高性价比）
- **1.0 - 2.0**: 良好
- **< 1.0**: 需谨慎
- **< 0**: 避免

### 下行波动率 (σ_down)
只考虑下跌时的波动，更准确地衡量损失风险
- **< 15%**: 低风险
- **15% - 20%**: 中低风险
- **20% - 25%**: 中高风险
- **> 25%**: 高风险

### β系数
个股相对行业的敏感度
- **β = 1.0**: 与行业同步
- **β > 1.0**: 比行业波动更大
- **β < 1.0**: 比行业波动更小

---

## 💡 典型使用场景

### 场景1: 对比多个标的

```yaml
companies:
  - name: "标的A"
    sector: "SEMI"
    expected_return: 0.40
    risk: {beta: 1.1, frag: 2.0}

  - name: "标的B"
    sector: "INTERNET"
    expected_return: 0.35
    risk: {beta: 1.0, frag: 1.5}
```

运行后系统自动排序，找出最优标的。

### 场景2: 分析混合行业公司

```yaml
  - name: "紫金矿业"
    sector_mix:
      NONFER: 0.6  # 60%有色
      GOLD: 0.4    # 40%黄金
```

系统自动按权重混合风险指标。

### 场景3: 使用估值模型

```yaml
  - name: "澜起科技"
    model:
      type: "PE"
      current_multiple: 88.0
      target_multiple: 45.0
      growth_12m: 0.30
      execution_prob: 0.90
```

系统自动计算期望收益。

---

## 📊 输出文件说明

### output.xlsx
完整的分析结果，包含：
- **排名**: 按值博率降序
- **σ总波动/σ下行**: 行业风险指标
- **MDD**: 最大回撤
- **ER原始/ER执行后**: 期望收益
- **损失风险**: Scheme C计算的总风险
- **值博率**: 最终排序依据

### ANALYSIS_SUMMARY.md
人类可读的分析报告，包含：
- Top 3投资机会
- 行业风险全景
- 风险警示
- 投资组合建议

---

## 🎯 最佳实践

1. **定期更新数据**: 每月运行一次分析
2. **对比历史结果**: 观察值博率变化趋势
3. **交叉验证**: 结合基本面分析
4. **风险控制**: 不要只看值博率，也要关注绝对风险
5. **分散投资**: 构建多标的组合

---

## ⚠️ 注意事项

- ⚠️ 历史数据不代表未来表现
- ⚠️ 模型假设可能与实际偏差
- ⚠️ 请结合自身风险承受能力
- ⚠️ 本工具仅供参考，不构成投资建议

---

## 🆘 常见问题

### Q: 数据获取失败？
A: 检查网络连接，或使用 `--force` 强制刷新缓存

### Q: 如何添加更多公司？
A: 编辑 `config/companies.yml`，添加新条目

### Q: 支持哪些市场？
A: A股（沪深）、港股，通过yfinance获取数据

### Q: 如何解读负值博率？
A: 负值博率表示期望收益为负，应避免投资

---

**下一步**: 查看 [README.md](README.md) 了解完整功能
