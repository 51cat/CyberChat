"""
tools/web_search.py - Tavily 互联网实时搜索工具
提供学术期刊信息的网络检索能力，作为本地数据库的实时信息补充与兜底手段。
"""

from langchain_core.tools import tool
from tavily import TavilyClient

from deep_paper import load_config

_cfg = load_config()
_tavily_client = TavilyClient(api_key=_cfg["tavily"]["api_key"])


def _format_tavily_results(results: dict, title: str) -> str:
    """统一格式化 Tavily 搜索结果。"""
    answer = results.get("answer", "")
    sources = []
    for r in results.get("results", [])[:5]:
        content_preview = r.get("content", "")[:200]
        sources.append(f"- [{r.get('title', 'N/A')}]({r.get('url', '')}): {content_preview}")

    output = f"## {title}\n\n"
    if answer:
        output += f"**摘要**: {answer}\n\n"
    output += "**来源**:\n" + "\n".join(sources)
    return output


@tool
def tavily_search_journal(journal_name: str) -> str:
    """在互联网上搜索某本学术期刊的详细信息，包括投稿须知、审稿周期、APC费用、收稿范围和最新影响因子。
    当需要获取期刊的实时信息时（如投稿链接、审稿速度、APC）使用此工具。

    Args:
        journal_name: 期刊名称，例如 "Nature Medicine"
    """
    try:
        results = _tavily_client.search(
            query=f"{journal_name} academic journal submission guidelines impact factor APC review time",
            max_results=10,
            topic="general",
            include_answer=True,
        )
        return _format_tavily_results(results, f"期刊搜索: {journal_name}")
    except Exception as e:
        return f"Tavily 搜索失败 (期刊: '{journal_name}'): {str(e)}"


@tool
def tavily_search_research_field(field_description: str) -> str:
    """在互联网上搜索某研究领域的推荐投稿期刊。当用户描述了研究方向且需要超出本地数据库范围的期刊推荐时使用。

    Args:
        field_description: 用英文描述的研究领域，例如 "lung cancer immunotherapy single-cell sequencing"
    """
    try:
        results = _tavily_client.search(
            query=f"best academic journals for {field_description} research paper submission 2024 2025 2026",
            max_results=10,
            topic="general",
            include_answer=True,
        )
        return _format_tavily_results(results, f"领域期刊搜索: {field_description}")
    except Exception as e:
        return f"Tavily 搜索失败 (领域: '{field_description}'): {str(e)}"


@tool
def tavily_search_general(query: str) -> str:
    """通用网络搜索兜底工具。当本地数据库和 OpenAlex 均无法提供所需信息时使用。

    Args:
        query: 搜索查询字符串
    """
    try:
        results = _tavily_client.search(
            query=query,
            max_results=10,
            topic="general",
            include_answer=True,
        )
        answer = results.get("answer", "")
        sources = []
        for r in results.get("results", [])[:5]:
            sources.append(f"- [{r.get('title', 'N/A')}]({r.get('url', '')}): {r.get('content', '')[:150]}")

        output = ""
        if answer:
            output += f"**摘要**: {answer}\n\n"
        output += "**来源**:\n" + "\n".join(sources)
        return output
    except Exception as e:
        return f"Tavily 搜索失败: {str(e)}"
