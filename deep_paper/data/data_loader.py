"""
data/data_loader.py - 数据预处理与加载模块
功能：
  1. 读取 data_2025/ 目录下的 cas.csv、jcr.csv 及 SCIE/SSCI/AHCI/ESCI.csv
  2. 清洗并合并各表，构建统一的期刊知识库 DataFrame
  3. 提供单例缓存，避免重复 IO
"""

import os
import pandas as pd

# 数据文件所在目录
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_2025")

CAS_FILE  = os.path.join(DATA_DIR, "cas.csv")
JCR_FILE  = os.path.join(DATA_DIR, "jcr.csv")
SCIE_FILE = os.path.join(DATA_DIR, "SCIE.csv")
SSCI_FILE = os.path.join(DATA_DIR, "SSCI.csv")
AHCI_FILE = os.path.join(DATA_DIR, "AHCI.csv")
ESCI_FILE = os.path.join(DATA_DIR, "ESCI.csv")


def _try_read_csv(filepath: str, sep: str = "\t") -> pd.DataFrame:
    """尝试以 utf-8 读取 CSV；若失败则回退到 gb18030 / latin1。"""
    for enc in ["utf-8", "gb18030", "latin1"]:
        try:
            df = pd.read_csv(filepath, encoding=enc, sep=sep)
            return df
        except (UnicodeDecodeError, Exception):
            continue
    raise RuntimeError(f"无法以任何已知编码读取文件: {filepath}")


def load_cas() -> pd.DataFrame:
    """加载并清洗 CAS 分区数据（Tab 分隔）。"""
    df = _try_read_csv(CAS_FILE, sep="\t")
    df.columns = [c.strip() for c in df.columns]

    rename_map = {}
    for col in df.columns:
        if "期刊" in col and "名" in col:
            rename_map[col] = "期刊名称"
        elif "分区" in col:
            rename_map[col] = "CAS分区"
    df = df.rename(columns=rename_map)

    if "期刊名称" in df.columns:
        df["期刊名称_标准"] = df["期刊名称"].astype(str).str.strip().str.upper()

    if "CAS分区" in df.columns:
        df["CAS分区"] = pd.to_numeric(df["CAS分区"], errors="coerce").astype("Int64")

    if "Top" in df.columns:
        df["是否Top"] = df["Top"].astype(str).str.strip().apply(
            lambda x: True if x in ["是", "Yes", "Y", "TRUE", "1"] else False
        )

    if "Open Access" in df.columns:
        df["是否OA"] = df["Open Access"].astype(str).str.strip().apply(
            lambda x: True if x in ["是", "Yes", "Y", "TRUE", "1"] else False
        )

    return df


def load_jcr() -> pd.DataFrame:
    """加载并清洗 JCR 分区数据（Tab 分隔），使用 2024分区 作为主分区。"""
    df = _try_read_csv(JCR_FILE, sep="\t")
    df.columns = [c.strip() for c in df.columns]

    rename_map = {}
    for col in df.columns:
        lower = col.lower()
        if "期刊" in col and "名" in col:
            rename_map[col] = "期刊名称"
        elif col == "2024JIF":
            rename_map[col] = "影响因子"
        elif col == "2024分区":
            rename_map[col] = "JCR分区"
        elif col == "Quartile":
            rename_map[col] = "Quartile_原始"
        elif col == "Total citation":
            rename_map[col] = "总被引"
        elif col == "JIF rank":
            rename_map[col] = "JIF排名"
        elif col == "Category":
            rename_map[col] = "学科类别"
        elif lower == "issn":
            rename_map[col] = "ISSN"
        elif lower == "eissn":
            rename_map[col] = "eISSN"
    df = df.rename(columns=rename_map)

    if "期刊名称" in df.columns:
        df["期刊名称_标准"] = df["期刊名称"].astype(str).str.strip().str.upper()

    return df


def load_wos_index() -> pd.DataFrame:
    """加载 SCIE/SSCI/AHCI/ESCI 四个索引文件，合并为统一的收录索引表。"""
    index_files = {
        "SCIE": SCIE_FILE,
        "SSCI": SSCI_FILE,
        "AHCI": AHCI_FILE,
        "ESCI": ESCI_FILE,
    }

    all_rows = []
    for index_name, filepath in index_files.items():
        if not os.path.exists(filepath):
            continue
        df = pd.read_csv(filepath, encoding="utf-8")
        df.columns = [c.strip() for c in df.columns]
        df = df.rename(columns={"Journal title": "期刊名称"})
        df["收录索引"] = index_name
        all_rows.append(df)

    if not all_rows:
        return pd.DataFrame(columns=["期刊名称_标准", "收录索引"])

    combined = pd.concat(all_rows, ignore_index=True)
    combined["期刊名称_标准"] = combined["期刊名称"].astype(str).str.strip().str.upper()

    # 按期刊聚合：合并多个索引标签，保留出版商等信息（取第一条）
    agg_index = combined.groupby("期刊名称_标准").agg(
        收录索引=("收录索引", lambda x: ", ".join(sorted(set(x)))),
        出版商=("Publisher name", "first"),
        语言=("Languages", "first"),
        WoS学科分类=("Web of Science Categories", "first"),
    ).reset_index()

    return agg_index


def load_merged_database() -> pd.DataFrame:
    """
    加载并合并 JCR + CAS + WoS 索引数据，构建完整的期刊知识库。
    返回合并后的 DataFrame。
    """
    jcr_df = load_jcr()
    cas_df = load_cas()
    wos_df = load_wos_index()

    # JCR ← CAS
    merged = pd.merge(
        jcr_df, cas_df,
        on="期刊名称_标准",
        how="outer",
        suffixes=("_JCR", "_CAS")
    )

    if "期刊名称_JCR" in merged.columns:
        merged["期刊名称"] = merged["期刊名称_JCR"].fillna(merged.get("期刊名称_CAS", ""))
    elif "期刊名称" not in merged.columns:
        merged["期刊名称"] = merged["期刊名称_标准"]

    # ← WoS Index
    merged = pd.merge(
        merged, wos_df,
        on="期刊名称_标准",
        how="left"
    )

    return merged


# ---- 模块级别缓存 ----
_DB_CACHE = None


def get_database() -> pd.DataFrame:
    """获取缓存的合并数据库（单例模式）。"""
    global _DB_CACHE
    if _DB_CACHE is None:
        _DB_CACHE = load_merged_database()
    return _DB_CACHE


if __name__ == "__main__":
    db = get_database()
    print(f"[OK] 数据库加载完成: {db.shape[0]} 条期刊记录, {db.shape[1]} 个字段")
    print(f"列名: {list(db.columns)}")
    print(db.head(5).to_string())
