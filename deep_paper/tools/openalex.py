"""
tools/openalex.py - OpenAlex 学术文献检索与交叉验证工具
通过 OpenAlex API 检索领域内高被引文章并统计期刊分布，
同时支持将推荐结果与本地 JCR/CAS 数据库交叉验证。
"""

import datetime
import urllib.parse
from collections import Counter, defaultdict

import pandas as pd
import requests
from langchain_core.tools import tool

from deep_paper.data import get_database


@tool
def recommend_journals_from_background(keywords: str) -> str:
    """根据用户论文的研究背景/关键词，通过 OpenAlex 学术数据库检索相关高被引文献，
    并统计这些文献最常发表的期刊，作为投稿推荐。
    当用户描述了自己论文的研究主题或背景并希望获得投稿建议时，使用此工具。

    Args:
        keywords: 英文学术关键词，用逗号分隔。例如 "single-cell RNA sequencing,tumor microenvironment,immunotherapy"
    """
    try:
        kws = [k.strip() for k in keywords.split(",") if k.strip()]
        if not kws:
            return "未提供有效的搜索关键词。"

        search_query = " AND ".join(kws)
        encoded_query = urllib.parse.quote(search_query)

        date_from = (datetime.date.today() - datetime.timedelta(days=365 * 3)).strftime("%Y-%m-%d")

        url = (
            f"https://api.openalex.org/works?"
            f"search={encoded_query}&"
            f"filter=from_publication_date:{date_from}&"
            f"sort=cited_by_count:desc&"
            f"per-page=100"
        )

        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return f"OpenAlex 查询出错 (HTTP {resp.status_code}): {resp.text[:200]}"

        data = resp.json()
        works = data.get("results", [])
        total_works = data.get("meta", {}).get("count", 0)

        if not works:
            return f"未找到与关键词 '{search_query}' 匹配的文献。"

        journal_counts = Counter()
        journal_citations = defaultdict(list)

        for work in works:
            primary_loc = work.get("primary_location") or {}
            source = primary_loc.get("source") or {}
            journal_name = source.get("display_name")

            if journal_name:
                journal_counts[journal_name] += 1
                citations = work.get("cited_by_count", 0)
                if citations is not None:
                    journal_citations[journal_name].append(citations)

        if not journal_counts:
            return "检索到文献但无法提取期刊来源信息。"

        top_journals = journal_counts.most_common(50)

        lines = [f"基于 OpenAlex 检索到的相关文献（展示 Top 100 篇中的高频期刊，共 {total_works} 篇）:\n"]
        for i, (name, count) in enumerate(top_journals, 1):
            cites = journal_citations.get(name, [])
            avg_cite = round(sum(cites) / len(cites), 1) if cites else "未知"
            lines.append(f"  {i}. {name} — 相关文章 {count} 篇, 平均被引 {avg_cite}")

        return "\n".join(lines)

    except requests.exceptions.Timeout:
        return "OpenAlex 查询超时（超过30秒）。请稍后重试或简化关键词。"
    except Exception as e:
        return f"调用 OpenAlex 查询时发生异常: {str(e)}"


@tool
def cross_validate_journals(journal_names: str) -> str:
    """交叉验证一组期刊名称在本地数据库中的详细指标（影响因子、分区等）。
    通常在 OpenAlex 推荐了一批期刊后，使用此工具核验这些期刊在 JCR/CAS 中的表现。

    Args:
        journal_names: 期刊名称列表，用英文逗号分隔。例如 "Nature Medicine,Cell Reports,Cancer Research"
    """
    db = get_database()
    names = [n.strip().upper() for n in journal_names.split(",") if n.strip()]

    if not names:
        return "请提供至少一个期刊名称。"

    results = []
    for name in names:
        match = db[db["期刊名称_标准"].str.contains(name, na=False)]
        if match.empty:
            results.append(f"- {name}: 未在本地数据库中找到记录")
        else:
            for _, row in match.head(3).iterrows():
                parts = [f"- {row.get('期刊名称', name)}"]
                if pd.notna(row.get("影响因子")):
                    parts.append(f"IF={row['影响因子']}")
                if pd.notna(row.get("JCR分区")):
                    parts.append(f"JCR={row['JCR分区']}")
                if pd.notna(row.get("CAS分区")):
                    parts.append(f"CAS={int(row['CAS分区'])}区")
                if row.get("是否Top") == True:
                    parts.append("Top")
                if row.get("是否OA") == True:
                    parts.append("OA")
                if pd.notna(row.get("收录索引")):
                    parts.append(f"收录={row['收录索引']}")
                results.append(" | ".join(parts))

    return f"交叉验证结果（{len(names)} 个期刊）:\n" + "\n".join(results)
