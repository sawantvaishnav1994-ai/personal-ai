import webbrowser, urllib.parse
from tools.registry import Tool, Risk


def _safe_web_url(raw):
    value = str(raw or '').strip()
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme.lower() not in {'http', 'https'} or not parsed.hostname:
        raise ValueError('only http/https web URLs are allowed')
    if parsed.username is not None or parsed.password is not None:
        raise ValueError('embedded URL credentials are not allowed')
    return value


def register(reg):
    reg.register(Tool(
        "open_url",
        "Open HTTP(S) URL; params: url",
        lambda p: (webbrowser.open(_safe_web_url(p["url"])) or True),
        Risk.EXTERNAL_SIDE_EFFECT,
    ))
    def search(p):
        q=urllib.parse.quote_plus(str(p["query"]))
        url=f"https://www.google.com/search?q={q}"
        webbrowser.open(url)
        return {"ok":True,"url":url}
    reg.register(Tool("web_search_browser","Open web search in browser; params: query",search,Risk.EXTERNAL_SIDE_EFFECT))
