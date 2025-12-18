#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: 物語、動画パスを引数として受け取り、ホームページを生成します。

import os
import sys
import datetime
try:
    import google.generativeai as genai
except ImportError:
    print("エラー: 'google-generativeai' ライブラリが見つかりません。", file=sys.stderr)
    sys.exit(1)

# --- 定数 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_FILE_PATH = os.path.join(PROJECT_ROOT, "api")
OUTPUT_DIR_PUBLIC = "/var/www/html/public/"

# --- APIキー取得 ---
def get_gemini_api_key() -> str | None:
    # ... (Implementation from previous version is fine)
    if os.path.exists(API_FILE_PATH):
        with open(API_FILE_PATH, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return os.getenv("GEMINI_API_KEY")

# --- AIコンテンツ生成 ---
def get_ai_story_html(api_key: str, story_content: str) -> str | None:
    """AIに物語のHTML版を生成させる"""
    print("AIに物語のHTML版をリクエスト中...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
以下の物語を、Webページに掲載するための魅力的なHTMLコンテンツにしてください。
- 物語の重要な部分を抜き出し、感動的な要約を作成します。
- `<h2>`タグで見出しを、`<p>`タグで段落を作成してください。
- 全体を `<div class="story-content">` タグで囲ってください。

--- 物語 ---
{story_content}

--- 出力 (HTMLのみ) ---
"""
        response = model.generate_content(prompt)
        # Markdown ```html ... ``` を削除
        if response.text.startswith('```html'):
            return response.text[7:-4].strip()
        return response.text
    except Exception as e:
        print(f"エラー: Gemini APIの呼び出し中にエラー: {e}", file=sys.stderr)
        return None

# --- メイン処理 ---
def main(story_content: str, story_name: str, video_filepath: str) -> str | None:
    """ホームページを生成し、成功すればファイルパスを、失敗すればNoneを返す。"""
    print("--- 進化するAIホームページコンテンツ生成ツール ---")

    # 1. 引数チェック
    if not all([story_content, story_name, video_filepath]):
        print("エラー: 必要な引数（物語内容, 物語名, 動画パス）が不足しています。", file=sys.stderr)
        return None

    # 2. APIキー取得
    api_key = get_gemini_api_key()
    if not api_key:
        print("エラー: Gemini APIキーが取得できませんでした。", file=sys.stderr)
        return None

    # 3. AIによるHTMLコンテンツ生成
    ai_html_content = get_ai_story_html(api_key, story_content)
    if not ai_html_content:
        print("エラー: AIによるコンテンツ生成に失敗しました。", file=sys.stderr)
        return None

    # 4. 完全なHTMLページを構築
    site_title = f"AI Saga Weaver - {story_name.replace('.md', '')}"
    video_filename = os.path.basename(video_filepath)
    
    video_player_html = f"""
<div class="video-container" style="margin: 2em 0; text-align: center;">
    <h3>本日のネオワールドサーガ</h3>
    <video controls preload="metadata" style="max-width: 100%; width: 800px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <source src="./{video_filename}" type="video/mp4">
        お使いのブラウザは動画タグをサポートしていません。
    </video>
</div>
"""

    full_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_title}</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; margin: 0; background-color: #f4f4f4; color: #333; }}
        .container {{ max-width: 960px; margin: auto; padding: 20px; background: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1, h2 {{ text-align: center; color: #444; }}
        .story-content p {{ text-indent: 1em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{site_title}</h1>
        {video_player_html}
        <hr>
        {ai_html_content}
    </div>
</body>
</html>
"""
    # 5. ファイルに保存
    output_filename = "ai_business_homepage.html"
    output_filepath = os.path.join(OUTPUT_DIR_PUBLIC, output_filename)
    os.makedirs(OUTPUT_DIR_PUBLIC, exist_ok=True)
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"ホームページコンテンツが {output_filepath} に生成されました。")
        return output_filepath
    except Exception as e:
        print(f"エラー: ホームページコンテンツの保存に失敗しました: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    print("このスクリプトはオーケストレーターから呼び出されることを想定しています。", file=sys.stderr)
    print("直接実行はできません。", file=sys.stderr)
    sys.exit(1)
