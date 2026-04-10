from deep_paper import load_config

try:
    _cfg = load_config()
except Exception:
    _cfg = {}

MODEL_NAME = _cfg.get("MODEL_NAME", " ")
OPENALEX_EMAIL = _cfg.get("OPENALEX_EMAIL", " ")
TAVILY_API_KEY = _cfg.get("TAVILY_API_KEY", " ")
OPENAI_API_KEY = _cfg.get("OPENAI_API_KEY", " ")
OPENAI_API_BASE = _cfg.get("OPENAI_API_BASE", " ")
DB_PATH = _cfg.get("DB_PATH", "")
