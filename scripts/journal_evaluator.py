#!/usr/bin/env python3
"""
期刊多维度评估引擎 v1.0
用于投稿选刊技能：对候选期刊进行多维度评分和排序
"""

import json
import os
from datetime import datetime
from typing import Optional


def evaluate_journal(journal_info: dict, user_requirements: dict) -> dict:
    """
    对单个期刊进行多维度评估
    
    Args:
        journal_info: 期刊信息字典，包含以下字段：
            - name: 期刊名称
            - level: 期刊级别（普刊/北大核心/CSSCI/科技核心等）
            - issn: ISSN号
            - cn: CN号
            -收录: dict，包含 cnki(知网), wanfang(万方), vip(维普) 的布尔值
            - impact_factor: 影响因子（可选）
            - review_cycle: 审稿周期（天）
            - publish_cycle: 见刊周期（天）
            - fee: 版面费（元）
            - fee_unit: 版面费单位（'page'每版/'article'每篇）
            - columns: 收稿方向/栏目列表
            - publish_frequency: 出版频率（月刊/双月刊等）
            - annual_articles: 年发文量
            - submit_url: 投稿直达链接（文映千秋学术网详情页URL或其他官方投稿链接）
            - contact_info: 投稿联系方式（官方投稿邮箱、在线投稿系统地址等）
            - host_unit: 主办单位
            - supervisor_unit: 主管单位
        user_requirements: 用户需求字典，包含以下字段：
            - research_direction: 研究方向/关键词列表
            - purpose: 投稿用途（职称评审/毕业/项目结题等）
            - level_requirement: 期刊级别要求
            - deadline: 最晚见刊日期（datetime或日期字符串）
            - budget: 版面费预算（元）
            - word_count: 文章字数
            - author_title: 作者职称
            - recognition: 单位认可要求（如需要哪些数据库收录）
    
    Returns:
        评估结果字典，包含各维度分数和总分
    """
    scores = {}
    
    # 维度1: 方向匹配度 (30%)
    scores['direction_match'] = _calc_direction_match(
        journal_info.get('columns', []),
        user_requirements.get('research_direction', [])
    )
    
    # 维度2: 单位认可度 (25%)
    scores['recognition'] = _calc_recognition(
        journal_info.get('收录', {}),
        journal_info.get('level', ''),
        user_requirements.get('recognition', {}),
        user_requirements.get('level_requirement', '')
    )
    
    # 维度3: 见刊时效 (20%)
    scores['timeliness'] = _calc_timeliness(
        journal_info.get('review_cycle', 30),
        journal_info.get('publish_cycle', 90),
        user_requirements.get('deadline', None),
        journal_info.get('publish_frequency', '')
    )
    
    # 维度4: 发表难度 (15%)
    scores['difficulty'] = _calc_difficulty(
        journal_info.get('level', ''),
        journal_info.get('annual_articles', 200),
        journal_info.get('impact_factor', 0),
        user_requirements.get('author_title', ''),
        user_requirements.get('word_count', 5000)
    )
    
    # 维度5: 性价比 (10%)
    scores['cost_effectiveness'] = _calc_cost_effectiveness(
        journal_info.get('fee', 0),
        journal_info.get('fee_unit', 'page'),
        journal_info.get('level', ''),
        user_requirements.get('budget', 999999)
    )
    
    # 加权总分
    weights = {
        'direction_match': 0.30,
        'recognition': 0.25,
        'timeliness': 0.20,
        'difficulty': 0.15,
        'cost_effectiveness': 0.10
    }
    
    total = sum(scores[k] * weights[k] for k in weights)
    scores['total'] = round(total, 1)
    
    # 推荐等级
    if scores['total'] >= 90:
        scores['grade'] = '强烈推荐'
    elif scores['total'] >= 75:
        scores['grade'] = '推荐投稿'
    elif scores['total'] >= 60:
        scores['grade'] = '可备选'
    else:
        scores['grade'] = '不推荐'
    
    # 风险标记
    scores['risks'] = _check_risks(journal_info)
    
    return scores


def batch_evaluate(candidates: list, user_requirements: dict, top_n: int = 10) -> list:
    """
    批量评估候选期刊并排序
    
    Args:
        candidates: 候选期刊信息字典列表
        user_requirements: 用户需求字典
        top_n: 返回前N个结果
    
    Returns:
        按综合得分降序排列的评估结果列表
    """
    results = []
    for journal in candidates:
        scores = evaluate_journal(journal, user_requirements)
        results.append({
            'journal': journal,
            'scores': scores
        })
    
    # 按总分降序排列
    results.sort(key=lambda x: x['scores']['total'], reverse=True)
    
    return results[:top_n]


def generate_report(results: list, user_requirements: dict, output_dir: str = './') -> str:
    """
    生成HTML选刊评估报告
    
    Args:
        results: batch_evaluate返回的评估结果列表
        user_requirements: 用户需求字典
        output_dir: 输出目录
    
    Returns:
        报告文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成雷达图
    radar_paths = _generate_radar_charts(results, output_dir)
    
    # 生成HTML报告
    html = _build_html_report(results, user_requirements, radar_paths, output_dir)
    
    report_path = os.path.join(output_dir, '选刊评估报告.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return report_path


# ========== 内部评分函数 ==========

def _calc_direction_match(columns: list, keywords: list) -> float:
    """计算方向匹配度 (0-100)"""
    if not columns or not keywords:
        return 50
    
    matched = 0
    for kw in keywords:
        for col in columns:
            if kw.lower() in col.lower() or col.lower() in kw.lower():
                matched += 1
                break
    
    ratio = matched / len(keywords)
    return min(100, ratio * 100)


def _calc_recognition(coverage: dict, level: str, user_recognition: dict, user_level: str) -> float:
    """计算单位认可度 (0-100)"""
    score = 0
    
    # 收录情况 (满分50)
    cnki = coverage.get('cnki', False)
    wanfang = coverage.get('wanfang', False)
    vip = coverage.get('vip', False)
    
    coverage_count = sum([cnki, wanfang, vip])
    score += coverage_count * 16.7  # 三网全收录=50分
    
    # 级别匹配 (满分30)
    level_rank = _get_level_rank(level)
    user_level_rank = _get_level_rank(user_level)
    
    if user_level_rank == 0:
        score += 30  # 用户无级别要求，不扣分
    elif level_rank >= user_level_rank:
        score += 30  # 期刊级别达到或超过要求
    else:
        score += max(0, 30 - (user_level_rank - level_rank) * 15)
    
    # 用户特定收录要求 (满分20)
    if user_recognition:
        required_dbs = user_recognition.get('required_dbs', [])
        for db in required_dbs:
            if coverage.get(db, False):
                score += 20 / max(len(required_dbs), 1)
    
    return min(100, score)


def _calc_timeliness(review_days: int, publish_days: int, deadline, frequency: str) -> float:
    """计算见刊时效 (0-100)"""
    total_days = review_days + publish_days
    
    if deadline is None:
        # 无时间限制，给出中性偏高分
        if total_days <= 90:
            return 95
        elif total_days <= 180:
            return 80
        else:
            return 65
    
    try:
        if isinstance(deadline, str):
            deadline = datetime.strptime(deadline, '%Y-%m-%d')
        days_left = (deadline - datetime.now()).days
    except:
        days_left = 180
    
    if days_left < 0:
        return 0  # 已过期
    
    time_ratio = total_days / max(days_left, 1)
    
    if time_ratio <= 0.5:
        return 95  # 大量时间裕量
    elif time_ratio <= 0.8:
        return 85  # 充裕
    elif time_ratio <= 1.0:
        return 70  # 刚好满足
    elif time_ratio <= 1.3:
        return 40  # 可能来不及
    else:
        return 10  # 大概率来不及


def _calc_difficulty(level: str, annual_articles: int, impact_factor: float, 
                     author_title: str, word_count: int) -> float:
    """计算发表难度 (0-100，分数越高表示越容易发表)"""
    score = 50  # 基准分
    
    # 期刊级别影响
    level_rank = _get_level_rank(level)
    if level_rank >= 4:
        score -= 25  # 顶级核心，难度大
    elif level_rank >= 3:
        score -= 15  # 一般核心
    elif level_rank >= 2:
        score -= 5   # 高质量普刊
    else:
        score += 5   # 普刊容易发
    
    # 年发文量影响
    if annual_articles >= 500:
        score += 15  # 发文量大，相对容易
    elif annual_articles >= 200:
        score += 5
    elif annual_articles < 50:
        score -= 15  # 发文量少，竞争激烈
    
    # 影响因子影响
    if impact_factor > 3:
        score -= 15
    elif impact_factor > 1:
        score -= 5
    
    return max(0, min(100, score))


def _calc_cost_effectiveness(fee: float, fee_unit: str, level: str, budget: float) -> float:
    """计算性价比 (0-100)"""
    if fee <= 0:
        return 90  # 无版面费或未提供，给高分
    
    # 归一化到每篇费用（假设一般文章2-3版）
    if fee_unit == 'page':
        total_fee = fee * 2.5  # 估算2.5版
    else:
        total_fee = fee
    
    # 判断费用是否在预算内
    if total_fee <= budget * 0.6:
        cost_score = 90  # 远低于预算
    elif total_fee <= budget:
        cost_score = 75  # 在预算内
    elif total_fee <= budget * 1.3:
        cost_score = 50  # 略超预算
    else:
        cost_score = 25  # 大超预算
    
    # 结合期刊级别判断性价比
    level_rank = _get_level_rank(level)
    if level_rank >= 3 and total_fee < 5000:
        cost_score += 10  # 核心期刊费用合理，加分
    elif level_rank <= 1 and total_fee > 3000:
        cost_score -= 10  # 普刊收费过高，减分
    
    return max(0, min(100, cost_score))


def _get_level_rank(level: str) -> int:
    """将期刊级别转为数字等级 (0-5, 越高越高级)"""
    if not level:
        return 1
    level_lower = level.lower()
    if 'sci' in level_lower or 'ssci' in level_lower:
        return 5
    if 'cssci' in level_lower and '扩展' not in level_lower:
        return 4
    if 'cscd' in level_lower:
        return 4
    if '北大核心' in level or '中文核心' in level or '科技核心' in level:
        return 3
    if 'cssci扩展' in level_lower:
        return 3
    if 'rccse' in level_lower:
        return 2
    if '国家级' in level:
        return 2
    if '省级' in level:
        return 1
    return 1  # 默认普刊


def _check_risks(journal_info: dict) -> list:
    """检查期刊风险项"""
    risks = []
    
    if not journal_info.get('cn'):
        risks.append('缺少CN号，可能是非法出版物')
    if not journal_info.get('issn'):
        risks.append('缺少ISSN号')
    
    if not journal_info.get('cn'):
        risks.append('缺少CN号，可能是非法出版物')
    coverage = journal_info.get('收录', {})
    if not coverage.get('cnki') and not coverage.get('wanfang') and not coverage.get('vip'):
        risks.append('未被知网、万方、维普任一数据库收录')
    if coverage.get('cnki') and not coverage.get('wanfang') and not coverage.get('vip'):
        risks.append('仅知网收录，部分单位可能不认可')
    
    annual = journal_info.get('annual_articles', 0)
    if annual > 1000:
        risks.append(f'年发文量{annual}篇，存在灌水嫌疑')
    
    fee = journal_info.get('fee', 0)
    if 0 < fee < 500:
        risks.append(f'版面费{fee}元显著低于市场均价，需警惕假刊')
    
    return risks


# ========== 报告生成函数 ==========

def _generate_radar_charts(results: list, output_dir: str) -> dict:
    """为每个推荐期刊生成评分雷达图"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    
    radar_dir = os.path.join(output_dir, 'radar_charts')
    os.makedirs(radar_dir, exist_ok=True)
    
    paths = {}
    categories = ['方向匹配度', '单位认可度', '见刊时效', '发表难度', '性价比']
    keys = ['direction_match', 'recognition', 'timeliness', 'difficulty', 'cost_effectiveness']
    
    for item in results[:5]:  # 只为前5名生成
        journal_name = item['journal'].get('name', '未知期刊')
        scores = item['scores']
        
        values = [scores.get(k, 0) for k in keys]
        values_plot = values + [values[0]]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles_plot = angles + [angles[0]]
        
        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
        ax.fill(angles_plot, values_plot, alpha=0.2, color='#4A90D9')
        ax.plot(angles_plot, values_plot, 'o-', linewidth=2, color='#4A90D9', markersize=5)
        ax.set_xticks(angles)
        ax.set_xticklabels(categories, fontsize=9)
        ax.set_ylim(0, 100)
        ax.set_title(f'{journal_name}\n综合: {scores["total"]}分', fontsize=11, pad=15)
        
        safe_name = journal_name.replace('/', '_').replace('\\', '_')
        img_path = os.path.join(radar_dir, f'radar_{safe_name}.png')
        plt.savefig(img_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        paths[journal_name] = img_path
    
    return paths


def _build_submit_button(journal: dict) -> str:
    """根据投稿链接信息生成投稿按钮HTML"""
    submit_url = journal.get('submit_url', '')
    wy_verified = journal.get('wy_verified', False)
    detail_url = journal.get('detail_url', '')

    if submit_url and 'win00.cn' in submit_url and wy_verified:
        # 通过名称+刊号双重验证 — 绿色投稿按钮 + 蓝色详情按钮
        detail_btn = ''
        if detail_url:
            detail_btn = (
                f'<a href="{detail_url}" target="_blank" '
                'style="display:inline-block; padding:10px 28px; background:#4A90D9; color:white; '
                'border-radius:6px; text-decoration:none; font-size:14px; font-weight:bold; margin-left:8px;">'
                '查看详情</a>'
            )
        html = (
            '<div style="margin-top: 15px; text-align: center; padding: 12px; background: #f0faf0; border-radius: 8px;">'
            f'<a href="{submit_url}" target="_blank" '
            'style="display:inline-block; padding:10px 28px; background:#27ae60; color:white; '
            'border-radius:6px; text-decoration:none; font-size:14px; font-weight:bold;">'
            '立即投稿</a>'
            f'{detail_btn}'
            '<br><span style="margin-top:6px; display:inline-block; color:#95a5a6; font-size:12px;">来源：文映千秋学术网</span>'
            '</div>'
        )
    elif submit_url and 'win00.cn' in submit_url and not wy_verified:
        # 未通过验证 — 静默不显示，不留任何提示
        html = ''
    elif submit_url:
        # 其他官方投稿渠道 — 蓝色按钮
        html = (
            '<div style="margin-top: 15px; text-align: center; padding: 12px; background: #f0f5ff; border-radius: 8px;">'
            f'<a href="{submit_url}" target="_blank" '
            'style="display:inline-block; padding:10px 28px; background:#4A90D9; color:white; '
            'border-radius:6px; text-decoration:none; font-size:14px; font-weight:bold;">'
            '前往投稿</a>'
            '</div>'
        )
    else:
        # 无投稿链接 — 灰色提示
        html = (
            '<div style="margin-top: 15px; text-align: center; padding: 10px; background: #f5f5f5; border-radius: 8px;">'
            '<span style="color:#bbb; font-size:13px;">暂无直达投稿链接，建议通过知网期刊导航查找官方投稿方式</span>'
            '</div>'
        )
    
    return html


def _build_html_report(results: list, user_requirements: dict, 
                       radar_paths: dict, output_dir: str) -> str:
    """构建HTML评估报告"""
    grade_colors = {
        '强烈推荐': '#27ae60',
        '推荐投稿': '#3498db',
        '可备选': '#f39c12',
        '不推荐': '#e74c3c'
    }
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 需求信息
    req_direction = ', '.join(user_requirements.get('research_direction', ['未指定']))
    req_purpose = user_requirements.get('purpose', '未指定')
    req_level = user_requirements.get('level_requirement', '未指定')
    req_deadline = str(user_requirements.get('deadline', '无'))
    req_budget = str(user_requirements.get('budget', '未指定'))
    
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="zh-CN">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<title>投稿选刊评估报告</title>',
        '</head>',
        '<body style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f6fa; color: #2c3e50;">',
        
        # 标题
        '<div style="text-align: center; padding: 30px 0; background: white; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">',
        f'<h1 style="color: #2c3e50; margin: 0;">投稿选刊评估报告</h1>',
        f'<p style="color: #7f8c8d; margin-top: 10px;">生成日期：{today}</p>',
        '</div>',
        
        # 需求摘要
        '<div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">',
        '<h2 style="color: #4A90D9; border-bottom: 2px solid #4A90D9; padding-bottom: 8px;">需求摘要</h2>',
        '<table style="width:100%; border-collapse: collapse;">',
        f'<tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #eee;"><b>研究方向</b></td><td style="padding: 10px; border: 1px solid #eee;">{req_direction}</td></tr>',
        f'<tr><td style="padding: 10px; border: 1px solid #eee;"><b>投稿用途</b></td><td style="padding: 10px; border: 1px solid #eee;">{req_purpose}</td></tr>',
        f'<tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #eee;"><b>期刊级别</b></td><td style="padding: 10px; border: 1px solid #eee;">{req_level}</td></tr>',
        f'<tr><td style="padding: 10px; border: 1px solid #eee;"><b>最晚见刊</b></td><td style="padding: 10px; border: 1px solid #eee;">{req_deadline}</td></tr>',
        f'<tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #eee;"><b>版面费预算</b></td><td style="padding: 10px; border: 1px solid #eee;">{req_budget}</td></tr>',
        '</table>',
        '</div>',
        
        # 对比总表
        '<div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">',
        '<h2 style="color: #4A90D9; border-bottom: 2px solid #4A90D9; padding-bottom: 8px;">推荐期刊对比</h2>',
        '<div style="overflow-x: auto;">',
        '<table style="width:100%; border-collapse: collapse; font-size: 14px;">',
        '<tr style="background: #4A90D9; color: white;">',
        '<th style="padding: 10px;">排名</th><th>期刊名称</th><th>级别</th><th>收录</th>',
        '<th>匹配度</th><th>综合分</th><th>审稿</th><th>费用</th><th>等级</th>',
        '</tr>',
    ]
    
    for i, item in enumerate(results):
        j = item['journal']
        s = item['scores']
        grade = s['grade']
        color = grade_colors.get(grade, '#95a5a6')
        bg = '#f8f9fa' if i % 2 == 0 else 'white'
        
        coverage_str = ''
        cnki = '✓' if j.get('收录', {}).get('cnki') else '✗'
        wf = '✓' if j.get('收录', {}).get('wanfang') else '✗'
        vip = '✓' if j.get('收录', {}).get('vip') else '✗'
        coverage_str = f'知{cnki} 万{wf} 维{vip}'
        
        fee_str = f"约{j.get('fee', '未知')}元" if j.get('fee') else '未知'
        review_str = f"{j.get('review_cycle', '?')}天" if j.get('review_cycle') else '未知'
        
        html_parts.append(
            f'<tr style="background: {bg};">'
            f'<td style="padding: 10px; text-align: center;">{i+1}</td>'
            f'<td style="padding: 10px;"><b>{j.get("name", "未知")}</b></td>'
            f'<td style="padding: 10px; text-align: center;">{j.get("level", "未知")}</td>'
            f'<td style="padding: 10px; text-align: center; font-size: 12px;">{coverage_str}</td>'
            f'<td style="padding: 10px; text-align: center;">{s.get("direction_match", 0):.0f}</td>'
            f'<td style="padding: 10px; text-align: center; font-weight: bold;">{s.get("total", 0):.0f}</td>'
            f'<td style="padding: 10px; text-align: center;">{review_str}</td>'
            f'<td style="padding: 10px; text-align: center;">{fee_str}</td>'
            f'<td style="padding: 10px; text-align: center; color: {color}; font-weight: bold;">{grade}</td>'
            f'</tr>'
        )
    
    html_parts.extend([
        '</table>',
        '</div>',
        '</div>',
    ])
    
    # 各期刊详细卡片
    for i, item in enumerate(results[:5]):
        j = item['journal']
        s = item['scores']
        grade = s['grade']
        color = grade_colors.get(grade, '#95a5a6')
        radar_img = radar_paths.get(j.get('name', ''))
        
        risks_html = ''
        if s.get('risks'):
            risk_items = ''.join(f'<li style="color: #e74c3c;">{r}</li>' for r in s['risks'])
            risks_html = f'<div style="margin-top: 10px; padding: 10px; background: #fff5f5; border: 1px solid #e74c3c; border-radius: 4px;"><b>⚠️ 风险提示：</b><ul style="margin: 5px 0 0 0;">{risk_items}</ul></div>'
        
        radar_html = ''
        if radar_img:
            import base64
            try:
                with open(radar_img, 'rb') as img_f:
                    b64 = base64.b64encode(img_f.read()).decode()
                radar_html = f'<div style="text-align: center; margin-top: 10px;"><img src="data:image/png;base64,{b64}" style="max-width: 250px;" alt="评分雷达图"></div>'
            except:
                pass
        
        card_html = '\n'.join([
            '<div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid {color};">'.format(color=color),
            f'<h3 style="color: {color}; margin-top: 0;">#{i+1} {j.get("name", "未知期刊")}</h3>',
            '<table style="width:100%; border-collapse: collapse; font-size: 14px;">',
            f'<tr style="background: #f8f9fa;"><td style="padding: 8px; border: 1px solid #eee;"><b>级别</b></td><td style="padding: 8px; border: 1px solid #eee;">{j.get("level", "未知")}</td><td style="padding: 8px; border: 1px solid #eee;"><b>ISSN</b></td><td style="padding: 8px; border: 1px solid #eee;">{j.get("issn", "未知")}</td></tr>',
            f'<tr><td style="padding: 8px; border: 1px solid #eee;"><b>主办单位</b></td><td colspan="3" style="padding: 8px; border: 1px solid #eee;">{j.get("host_unit", "未知")}</td></tr>',
            f'<tr style="background: #f8f9fa;"><td style="padding: 8px; border: 1px solid #eee;"><b>CN号</b></td><td style="padding: 8px; border: 1px solid #eee;">{j.get("cn", "未知")}</td><td style="padding: 8px; border: 1px solid #eee;"><b>出版周期</b></td><td style="padding: 8px; border: 1px solid #eee;">{j.get("publish_frequency", "未知")}</td></tr>',
            f'<tr><td style="padding: 8px; border: 1px solid #eee;"><b>审稿周期</b></td><td style="padding: 8px; border: 1px solid #eee;">{j.get("review_cycle", "?")}天</td><td style="padding: 8px; border: 1px solid #eee;"><b>见刊周期</b></td><td style="padding: 8px; border: 1px solid #eee;">{j.get("publish_cycle", "?")}天</td></tr>',
            f'<tr style="background: #f8f9fa;"><td style="padding: 8px; border: 1px solid #eee;"><b>版面费</b></td><td style="padding: 8px; border: 1px solid #eee;">约{j.get("fee", "未知")}元/{j.get("fee_unit", "版")}</td><td style="padding: 8px; border: 1px solid #eee;"><b>影响因子</b></td><td style="padding: 8px; border: 1px solid #eee;">{j.get("impact_factor", "未知")}</td></tr>',
            f'<tr><td style="padding: 8px; border: 1px solid #eee;"><b>收稿方向</b></td><td colspan="3" style="padding: 8px; border: 1px solid #eee;">{", ".join(j.get("columns", ["未知"]))}</td></tr>',
            f'<tr style="background: #f8f9fa;"><td style="padding: 8px; border: 1px solid #eee;"><b>投稿方式</b></td><td colspan="3" style="padding: 8px; border: 1px solid #eee;">{j.get("contact_info", "暂无")}</td></tr>',
            '</table>',
            f'<div style="margin-top: 10px; padding: 10px; background: #f0f8ff; border-radius: 4px;"><b>评分明细：</b> 方向匹配{s.get("direction_match",0):.0f} | 认可度{s.get("recognition",0):.0f} | 时效{s.get("timeliness",0):.0f} | 难度{s.get("difficulty",0):.0f} | 性价比{s.get("cost_effectiveness",0):.0f} | <b>综合{s.get("total",0):.0f}分</b></div>',
            risks_html,
            radar_html,
            _build_submit_button(j),
            '</div>',
        ])
        html_parts.append(card_html)
    
    # 风险提示区
    all_risks = []
    for item in results:
        for r in item['scores'].get('risks', []):
            if r not in all_risks:
                all_risks.append(r)
    
    if all_risks:
        risk_items = ''.join(f'<li>{r}</li>' for r in all_risks)
        risk_html = '\n'.join([
            '<div style="background: #fff8e1; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #ffc107; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">',
            '<h2 style="color: #f57c00;">⚠️ 综合风险提示</h2>',
            f'<ul style="line-height: 1.8;">{risk_items}</ul>',
            '<p style="color: #666; font-size: 13px; margin-top: 10px;">建议投稿前通过国家新闻出版署（nppa.gov.cn）和知网期刊导航交叉验证期刊真实性。</p>',
            '</div>',
        ])
        html_parts.append(risk_html)
    
    # 免责声明
    html_parts.extend([
        '<div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">',
        '<p style="color: #95a5a6; font-size: 12px; line-height: 1.6;">',
        '<b>免责声明：</b>本报告基于公开数据库检索结果生成，期刊信息（审稿周期、版面费、收录情况等）可能随时间变化。实际投稿前请通过官方渠道确认最新信息。版面费为参考价格，以编辑部通知为准。建议投稿前确认所在单位最新职称评审文件中对期刊的具体认可要求。',
        '</p>',
        '</div>',
        '</body>',
        '</html>',
    ])
    
    return '\n'.join(html_parts)


if __name__ == '__main__':
    # 演示用法
    demo_journal = {
        'name': '语文教学与研究',
        'level': '省级普刊',
        'issn': '1004-0497',
        'cn': '42-1026/G4',
        '收录': {'cnki': True, 'wanfang': True, 'vip': True},
        'impact_factor': 0.35,
        'review_cycle': 5,
        'publish_cycle': 60,
        'fee': 1200,
        'fee_unit': 'page',
        'columns': ['语文教学', '阅读研究', '写作教学', '教材分析'],
        'publish_frequency': '月刊',
        'annual_articles': 180,
        'host_unit': '华中师范大学',
        'supervisor_unit': '教育部',
        'submit_url': 'https://www.win00.cn/client/submission_wizard.php?type=journal&resource_id=339',
        'detail_url': 'https://www.win00.cn/journal-339.html',
        'contact_info': '在线投稿 | 邮箱：ywjs@ccnu.edu.cn'
    }
    
    demo_req = {
        'research_direction': ['语文教学', '阅读教学'],
        'purpose': '职称评审（中级）',
        'level_requirement': '普刊',
        'deadline': '2026-10-01',
        'budget': 3000,
        'word_count': 5000,
        'author_title': '中学一级教师',
        'recognition': {'required_dbs': ['cnki', 'wanfang']}
    }
    
    scores = evaluate_journal(demo_journal, demo_req)
    print(json.dumps(scores, ensure_ascii=False, indent=2))
