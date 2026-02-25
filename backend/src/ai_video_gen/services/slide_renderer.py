"""スライドレンダリングサービス"""

import html
import re
from pathlib import Path

# テンプレートディレクトリ
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def render_slide_html(visual_spec: dict, section_type: str) -> str:
    """visual_specからスライドHTMLを生成"""
    template_path = TEMPLATE_DIR / "slide.html"
    template = template_path.read_text(encoding="utf-8")

    content = _generate_content(visual_spec, section_type)
    return template.replace("{{ content }}", content)


def _generate_content(visual_spec: dict, section_type: str) -> str:
    """セクションタイプに応じたコンテンツHTML生成"""
    if section_type == "title":
        title = html.escape(visual_spec.get("title", ""))
        subtitle = html.escape(visual_spec.get("subtitle", ""))
        return f'''
        <div class="title-slide">
            <h1>{title}</h1>
            <p class="subtitle">{subtitle}</p>
        </div>
        '''

    elif section_type == "slide":
        heading = html.escape(visual_spec.get("heading", ""))
        bullets = visual_spec.get("bullets", [])
        bullets_html = "\n".join(
            f"<li>{html.escape(b)}</li>" for b in bullets
        )
        return f'''
        <div class="content-slide">
            <h2>{heading}</h2>
            <ul>{bullets_html}</ul>
        </div>
        '''

    elif section_type in ("code", "code_typing"):
        language = visual_spec.get("language", "python")
        code = visual_spec.get("code", "")
        highlighted_code = _highlight_code(code, language)
        return f'''
        <div class="code-slide">
            <h2>{html.escape(language.upper())}</h2>
            <pre><code>{highlighted_code}</code></pre>
        </div>
        '''

    elif section_type == "summary":
        points = visual_spec.get("points", [])
        points_html = "\n".join(
            f"<li>{html.escape(p)}</li>" for p in points
        )
        return f'''
        <div class="summary-slide">
            <h2>まとめ</h2>
            <ul>{points_html}</ul>
        </div>
        '''

    elif section_type == "diagram":
        description = html.escape(visual_spec.get("description", ""))
        return f'''
        <div class="content-slide">
            <h2>図解</h2>
            <p style="font-size: 32px; text-align: center;">{description}</p>
        </div>
        '''

    else:
        # 汎用表示
        import json
        content = html.escape(json.dumps(visual_spec, ensure_ascii=False, indent=2))
        return f'''
        <div class="content-slide">
            <pre style="font-size: 24px;">{content}</pre>
        </div>
        '''


def _highlight_code(code: str, language: str) -> str:
    """簡易シンタックスハイライト"""
    code = html.escape(code)

    if language == "python":
        # キーワード
        keywords = r'\b(def|class|if|else|elif|for|while|return|import|from|as|try|except|with|in|not|and|or|True|False|None)\b'
        code = re.sub(keywords, r'<span class="keyword">\1</span>', code)
        # 文字列
        code = re.sub(r'(&quot;.*?&quot;|&#x27;.*?&#x27;)', r'<span class="string">\1</span>', code)
        code = re.sub(r"('.*?'|\".*?\")", r'<span class="string">\1</span>', code)
        # コメント
        code = re.sub(r'(#.*?)$', r'<span class="comment">\1</span>', code, flags=re.MULTILINE)
        # 関数呼び出し
        code = re.sub(r'\b(\w+)\(', r'<span class="function">\1</span>(', code)

    elif language == "javascript":
        keywords = r'\b(const|let|var|function|if|else|for|while|return|import|export|from|async|await|try|catch|new|class|this|true|false|null|undefined)\b'
        code = re.sub(keywords, r'<span class="keyword">\1</span>', code)
        code = re.sub(r"('.*?'|\".*?\"|`.*?`)", r'<span class="string">\1</span>', code)
        code = re.sub(r'(//.*?)$', r'<span class="comment">\1</span>', code, flags=re.MULTILINE)
        code = re.sub(r'\b(\w+)\(', r'<span class="function">\1</span>(', code)

    return code


def generate_slide_data_url(visual_spec: dict, section_type: str) -> str:
    """スライドHTMLをdata URLとして返す（プレビュー用）"""
    import base64
    html_content = render_slide_html(visual_spec, section_type)
    encoded = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    return f"data:text/html;base64,{encoded}"
