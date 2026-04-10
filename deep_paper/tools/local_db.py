"""
tools/local_db.py - 本地期刊数据库查询工具
提供基于本地 JCR/CAS 合并数据库的多维度查询功能。
"""

from typing import Optional

import pandas as pd
from langchain_core.tools import tool

from deep_paper.data import get_database


def _df_to_brief(df: pd.DataFrame, max_rows: int = 30) -> str:
    """将 DataFrame 格式化为简洁的文本摘要，供大模型阅读。"""
    if df.empty:
        return "未找到符合条件的期刊。"

    total = len(df)
    show_df = df.head(max_rows)

    display_cols = []
    for col in ["期刊名称", "影响因子", "JCR分区", "CAS分区", "是否Top", "是否OA", "收录索引", "学科类别", "ISSN"]:
        if col in show_df.columns:
            display_cols.append(col)

    if not display_cols:
        display_cols = list(show_df.columns[:6])

    result_lines = []
    for _, row in show_df[display_cols].iterrows():
        parts = []
        for col in display_cols:
            val = row[col]
            if pd.notna(val):
                parts.append(f"{col}: {val}")
        result_lines.append(" | ".join(parts))

    header = f"共找到 {total} 条结果"
    if total > max_rows:
        header += f"（仅展示前 {max_rows} 条）"
    header += ":\n"

    return header + "\n".join(result_lines)


@tool
def search_journal_by_name(query: str) -> str:
    """根据期刊名称（支持模糊搜索和精确搜索）查询期刊的全部信息，包括影响因子、JCR分区、中科院分区、是否为Top、是否为OA等。
    当用户想要查找某本具体期刊的信息时使用此工具。

    Args:
        query: 期刊名称关键词，可以是完整名称或部分名称。例如 "Nature", "Lancet", "Cell"
    """
    db = get_database()
    query_upper = query.strip().upper()

    exact = db[db["期刊名称_标准"] == query_upper]
    if not exact.empty:
        return _df_to_brief(exact)

    fuzzy = db[db["期刊名称_标准"].str.contains(query_upper, na=False)]
    if fuzzy.empty:
        return f"未找到名称含有 '{query}' 的期刊。请尝试使用英文全称或缩写搜索。"

    return _df_to_brief(fuzzy)


@tool
def filter_by_jcr_quartile(quartile: str) -> str:
    """按 JCR 分区筛选期刊列表。用户想要查看某个 JCR 分区的期刊时使用。

    Args:
        quartile: JCR 分区，例如 "Q1", "Q2", "Q3", "Q4"
    """
    db = get_database()
    q = quartile.strip().upper()
    if q not in ["Q1", "Q2", "Q3", "Q4"]:
        return f"无效的 JCR 分区 '{quartile}'。请输入 Q1, Q2, Q3 或 Q4。"

    filtered = db[db["JCR分区"] == q]
    return _df_to_brief(filtered)


@tool
def filter_by_cas_partition(partition: int) -> str:
    """按中科院分区筛选期刊列表。用户想要查看 CAS 某个分区（如1区、2区）的期刊时使用。

    Args:
        partition: 中科院分区编号，1 表示1区，2 表示2区，3 表示3区，4 表示4区
    """
    db = get_database()
    if partition not in [1, 2, 3, 4]:
        return f"无效的中科院分区 '{partition}'。请输入 1, 2, 3 或 4。"

    filtered = db[db["CAS分区"] == partition]
    return _df_to_brief(filtered)


@tool
def filter_top_journals() -> str:
    """获取所有被中科院标记为 Top 的顶级期刊列表。当用户询问"有哪些Top期刊"或"推荐Top期刊"时使用。"""
    db = get_database()
    filtered = db[db["是否Top"] == True]
    return _df_to_brief(filtered)


@tool
def filter_by_category(category: str) -> str:
    """按学科类别（Category）筛选期刊。用户想查询某个特定学术领域的期刊时使用。

    Args:
        category: 学科类别关键词，例如 "ONCOLOGY", "MICROBIOLOGY", "CELL BIOLOGY", "IMMUNOLOGY"
    """
    db = get_database()
    cat_upper = category.strip().upper()
    filtered = db[db["学科类别"].str.contains(cat_upper, na=False, case=False)]
    return _df_to_brief(filtered)


@tool
def complex_journal_search(
    min_jif: Optional[float] = None,
    max_jif: Optional[float] = None,
    cas_partition: Optional[int] = None,
    jcr_quartile: Optional[str] = None,
    is_top: Optional[bool] = None,
    is_oa: Optional[bool] = None,
    category: Optional[str] = None,
) -> str:
    """复合条件高级检索期刊。当用户有多个筛选条件时使用此工具，例如"帮我找影响因子大于5、中科院1区、Top的期刊"。

    Args:
        min_jif: 最低影响因子（JIF），例如 5.0
        max_jif: 最高影响因子（JIF），例如 50.0
        cas_partition: 中科院分区编号（1/2/3/4），例如 1
        jcr_quartile: JCR分区（Q1/Q2/Q3/Q4），例如 "Q1"
        is_top: 是否为中科院 Top 期刊，True 或 False
        is_oa: 是否为开放获取（Open Access），True 或 False
        category: 学科类别关键词，例如 "ONCOLOGY"
    """
    db = get_database()
    mask = pd.Series([True] * len(db))

    if min_jif is not None:
        mask &= pd.to_numeric(db["影响因子"], errors="coerce") >= min_jif
    if max_jif is not None:
        mask &= pd.to_numeric(db["影响因子"], errors="coerce") <= max_jif
    if cas_partition is not None:
        mask &= db["CAS分区"] == cas_partition
    if jcr_quartile is not None:
        mask &= db["JCR分区"] == jcr_quartile.strip().upper()
    if is_top is not None:
        mask &= db["是否Top"] == is_top
    if is_oa is not None:
        mask &= db["是否OA"] == is_oa
    if category is not None:
        mask &= db["学科类别"].str.contains(category.strip().upper(), na=False, case=False)

    filtered = db[mask]

    if "影响因子" in filtered.columns:
        filtered = filtered.copy()
        filtered["_jif_num"] = pd.to_numeric(filtered["影响因子"], errors="coerce")
        filtered = filtered.sort_values("_jif_num", ascending=False).drop(columns=["_jif_num"])

    return _df_to_brief(filtered)


@tool
def filter_by_wos_index(index_name: str) -> str:
    """按 Web of Science 收录索引筛选期刊列表。用户想要查看属于特定收录索引的期刊时使用。

    Args:
        index_name: 收录索引名称，例如 "SCIE", "SSCI", "AHCI", "ESCI"
    """
    db = get_database()
    idx_upper = index_name.strip().upper()
    if idx_upper not in ["SCIE", "SSCI", "AHCI", "ESCI"]:
        return f"无效的收录索引 '{index_name}'。请输入 SCIE, SSCI, AHCI 或 ESCI。"

    filtered = db[db["收录索引"].str.contains(idx_upper, na=False)]
    return _df_to_brief(filtered)
