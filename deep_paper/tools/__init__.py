"""
tools/__init__.py - 工具包统一出口
汇总三个子模块的 @tool 函数，并提供按功能分组的工具列表，供 Agent 按需调度。
"""

from .local_db import (
    search_journal_by_name,
    filter_by_jcr_quartile,
    filter_by_cas_partition,
    filter_top_journals,
    filter_by_category,
    complex_journal_search,
    filter_by_wos_index,
)
from .openalex import (
    recommend_journals_from_background,
    cross_validate_journals,
)
from .web_search import (
    tavily_search_journal,
    tavily_search_research_field,
    tavily_search_general,
)

# 按子 Agent 分组导出（供 agents/builder.py 使用）
LOCAL_DB_TOOLS = [
    search_journal_by_name,
    filter_by_jcr_quartile,
    filter_by_cas_partition,
    filter_top_journals,
    filter_by_category,
    complex_journal_search,
    filter_by_wos_index,
]

OPENALEX_TOOLS = [
    recommend_journals_from_background,
    cross_validate_journals,
]

TAVILY_TOOLS = [
    tavily_search_journal,
    tavily_search_research_field,
    tavily_search_general,
]

# 全部工具（供 ReAct 兜底 Agent 使用）
ALL_TOOLS = LOCAL_DB_TOOLS + OPENALEX_TOOLS + TAVILY_TOOLS

__all__ = [
    "LOCAL_DB_TOOLS",
    "OPENALEX_TOOLS",
    "TAVILY_TOOLS",
    "ALL_TOOLS",
]
