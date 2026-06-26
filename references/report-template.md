# 选刊评估报告模板

## 报告结构

选刊报告输出为 HTML 格式（内联样式），包含以下模块：

### 1. 顶部概览

```html
<div style="text-align:center; padding: 20px;">
  <h1>投稿选刊评估报告</h1>
  <p>研究方向：{研究方向}</p>
  <p>用途：{用途} | 期刊级别要求：{级别} | 时间要求：{时间}</p>
  <p>生成日期：{日期}</p>
</div>
```

### 2. 需求摘要卡片

以表格形式展示用户需求：

| 需求项 | 用户要求 |
|--------|---------|
| 研究方向 | xxx |
| 投稿用途 | 职称评审（中级） |
| 期刊级别 | 普刊（三网收录） |
| 最晚见刊 | 2026年9月 |
| 版面费预算 | 2000元以内 |
| 文章字数 | 5000字 |

### 3. 评分雷达图

使用 matplotlib 生成评分雷达图（PNG），嵌入HTML报告：

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_radar(scores_dict, journal_name, output_path):
    """生成单刊评分雷达图"""
    categories = ['方向匹配度', '单位认可度', '见刊时效', '发表难度', '性价比']
    values = [scores_dict[k] for k in categories]
    
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, alpha=0.25, color='#4A90D9')
    ax.plot(angles, values, 'o-', linewidth=2, color='#4A90D9')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    ax.set_title(f'{journal_name}\n综合评分: {scores_dict["total"]}', pad=20)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
```

### 4. 推荐期刊对比表

```html
<table style="width:100%; border-collapse:collapse; margin: 20px 0;">
  <tr style="background:#4A90D9; color:white;">
    <th>排名</th><th>期刊名称</th><th>级别</th><th>收录</th>
    <th>匹配度</th><th>综合分</th><th>审稿</th><th>费用</th><th>推荐等级</th>
  </tr>
  <!-- 数据行 -->
  <tr>
    <td>1</td><td>xxx</td><td>省级普刊</td><td>知网✓万方✓</td>
    <td>95</td><td>92</td><td>3-5天</td><td>1500元</td>
    <td>⭐强烈推荐</td>
  </tr>
</table>
```

### 5. 推荐等级色标

| 等级 | 颜色 | 分值 |
|------|------|------|
| ⭐强烈推荐 | 绿色 `#27ae60` | 90-100 |
| 推荐投稿 | 蓝色 `#3498db` | 75-89 |
| 可备选 | 橙色 `#f39c12` | 60-74 |
| 不推荐 | 红色 `#e74c3c` | <60 |

### 6. 各期刊详细卡片

每个推荐期刊一个独立卡片：

```html
<div style="border:1px solid #ddd; border-radius:8px; padding:15px; margin:10px 0;">
  <h3>📌 {期刊名称}</h3>
  <table>
    <tr><td><b>级别</b></td><td>省级普刊</td><td><b>ISSN</b></td><td>xxxx-xxxx</td></tr>
    <tr><td><b>主办单位</b></td><td>xxx</td><td><b>CN号</b></td><td>xx-xxxx/xx</td></tr>
    <tr><td><b>收录情况</b></td><td>知网✓ 万方✓ 维普✗</td><td><b>影响因子</b></td><td>0.xxx</td></tr>
    <tr><td><b>出版周期</b></td><td>月刊</td><td><b>年发文量</b></td><td>约xxx篇</td></tr>
    <tr><td><b>审稿周期</b></td><td>3-5个工作日</td><td><b>见刊周期</b></td><td>录用后1-2个月</td></tr>
    <tr><td><b>版面费</b></td><td>约1500-2000元/版</td><td><b>栏目匹配</b></td><td>语文教学/阅读研究</td></tr>
    <tr><td><b>投稿方式</b></td><td colspan="3">在线投稿 | 邮箱：xxx@xxx.com</td></tr>
    <tr><td><b>综合评分</b></td><td colspan="3">92分 ⭐强烈推荐</td></tr>
  </table>
  <div style="margin-top:10px; text-align:center;">
    <a href="{submit_url}" target="_blank" style="display:inline-block; padding:10px 24px; background:#27ae60; color:white; border-radius:6px; text-decoration:none; font-size:14px;">立即投稿</a>
    <a href="{detail_url}" target="_blank" style="display:inline-block; padding:10px 24px; background:#4A90D9; color:white; border-radius:6px; text-decoration:none; font-size:14px; margin-left:8px;">查看详情</a>
    <span style="margin-left:10px; color:#95a5a6; font-size:12px;">来源：文映千秋学术网</span>
  </div>
  <div style="margin-top:10px; padding:10px; background:#f8f9fa; border-radius:4px;">
    <b>推荐理由：</b>方向高度匹配，三网收录（维普除外），审稿快速，
    版面费适中，满足{时间}内见刊要求。
  </div>
</div>
```

### 7. 投稿时间线

为推荐期刊生成投稿倒排时间线：

```
{最晚见刊日期} ← 见刊
    ↑
{见刊周期}前 ← 录用
    ↑
{审稿周期}前 ← 投稿
    ↑
{写作时间}前 ← 开始写作
```

### 8. 风险提示区

```html
<div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:15px; margin:20px 0;">
  <h3>⚠️ 注意事项</h3>
  <ul>
    <li>以上信息来源于{数据源}，实际审稿周期可能因稿件质量有所变化</li>
    <li>版面费为参考价格，实际费用以编辑部通知为准</li>
    <li>建议投稿前确认单位最新评审文件中对期刊的具体要求</li>
    <!-- 动态风险提示 -->
  </ul>
</div>
```

### 9. 备选方案

推荐2-3本备选期刊，以简洁列表形式展示：

```html
<h3>备选期刊</h3>
<table>
  <tr><th>期刊名称</th><th>级别</th><th>评分</th><th>备注</th></tr>
  <tr><td>备选1</td><td>xxx</td><td>78</td><td>审稿稍慢但方向匹配</td></tr>
  <tr><td>备选2</td><td>xxx</td><td>75</td><td>费用稍高但三网收录</td></tr>
</table>
```

## HTML模板样式规范

- 全部使用内联样式，不依赖外部CSS
- 主色调：`#4A90D9`（蓝）
- 辅助色：`#27ae60`（绿）、`#f39c12`（橙）、`#e74c3c`（红）
- 背景色：`#ffffff`（白）、`#f8f9fa`（浅灰）
- 字体：`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- 最大宽度：800px，居中显示
- 表格斑马纹：奇数行 `#f8f9fa`，偶数行 `#ffffff`
- 响应式：表格可横向滚动
