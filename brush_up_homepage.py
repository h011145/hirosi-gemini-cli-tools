#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: 既存のHTMLファイルをGemini APIでブラッシュアップします。

import os
import sys
import datetime
import feedparser
import re # reモジュールをインポート
try:
    import google.generativeai as genai
except ImportError:
    print("エラー: 'google-generativeai' ライブラリが見つかりません。", file=sys.stderr)
    print("以下のコマンドでインストールしてください:", file=sys.stderr)
    print("pip install google-generativeai", file=sys.stderr)
    sys.exit(1)


# --- パスとURL設定 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_FILE_PATH = os.path.join(PROJECT_ROOT, "api")
DEFAULT_HTML_PATH = "/var/www/html/public/ai_business_homepage.html"
NHK_RSS_FEED_URL = "https://news.web.nhk/n-data/conf/na/rss/cat0.xml"


# --- APIキー取得関数 ---
def get_gemini_api_key() -> str:
    """APIキーを取得する (apiファイル > 環境変数)"""
    if os.path.exists(API_FILE_PATH):
        with open(API_FILE_PATH, 'r', encoding='utf-8') as f:
            api_key = f.read().strip()
        if api_key:
            print(f"APIキーをファイル '{API_FILE_PATH}' から読み込みました。")
            return api_key
        else:
            print(f"警告: '{API_FILE_PATH}' は空です。", file=sys.stderr)

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("APIキーを環境変数 'GEMINI_API_KEY' から読み込みました。")
        return api_key
    
    return ""

# --- RSSフィード取得関数 ---
def get_latest_rss_headline(rss_url: str) -> str:
    """指定されたRSSフィードから最新記事の見出しを取得する"""
    print(f"RSSフィードを取得中: {rss_url}")
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            latest_title = feed.entries[0].title
            print(f"最新の見出しを取得しました: {latest_title}")
            return latest_title
        print("警告: RSSフィードにエントリがありませんでした。", file=sys.stderr)
        return "最新ニュースはありません。"
    except Exception as e:
        print(f"エラー: RSSフィードの取得または解析中にエラーが発生しました: {e}", file=sys.stderr)
        return "最新ニュースの取得に失敗しました。"

# --- Gemini API 呼び出し関数 ---
def call_gemini_api_for_brush_up(api_key: str, original_html_content: str, user_instruction: str) -> str:
    print("\n--- Gemini APIにブラッシュアップをリクエスト中 ---")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt_parts = [
            "あなたは、既存のHTMLコンテンツをユーザーの指示に基づいてブラッシュアップする専門家です。",
            "元のHTMLコンテンツの構造と内容を尊重しつつ、より魅力的で洗練されたHTMLを出力してください。",
            "**デザイン要件:**",
            "* 堅牢でシックな雰囲気を保ってください。",
            "* 画像は直接埋め込まず、視覚情報は動画サイトへのリンク（埋め込みコードではない）で表現してください。",
            "* 上記要件以外で、HTMLやスタイルで表現可能な部分は、積極的に活用し、効果的に色（CSSの `color` や `background-color` など）も使用して、魅力的で分かりやすいコンテンツにしてください。",
            "**出力形式:**",
            "* 最終的なHTMLファイル全体（`<!DOCTYPE html>`から`</html>`まで）を生成してください。ただし、headタグ内の`<base href=...>`は現状維持してください。",
            "* CSSは`<style>`タグ内に記述するか、HTML要素にインラインスタイルで適用してください。",
            "* JavaScriptは含めないでください。",
            "* HTML要素は意味論的に正しいものを使用し、Bootstrapなどのフレームワークは考慮せず、プレーンなHTML構造でお願いします。",
            "",
            "--- 元のHTMLコンテンツ ---",
            original_html_content,
            "",
            "--- ユーザーからのブラッシュアップ指示 ---",
            user_instruction,
            "",
            "--- ブラッシュアップ後のHTML ---"
        ]

        full_prompt = "\n".join(prompt_parts)
        print("--- Gemini API呼び出し中...しばらくお待ちください。 ---")
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"エラー: Gemini APIの呼び出し中にエラーが発生しました: {e}", file=sys.stderr)
        return ""

# --- ユーティリティ関数 ---
def strip_markdown_code_fences(text: str) -> str:
    """Gemini APIの応答からMarkdownのコードブロック(```html ... ```)のみを抽出する"""
    # ```html で始まり ``` で終わるブロックを探す
    match = re.search(r'```html\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        # マッチした内側のコンテンツを返す
        return match.group(1).strip()
    
    # もし上記パターンにマッチしないが、``` が存在する場合は、その内側を試す
    match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # それでも見つからない場合は、元のテキストをそのまま返す（フォールバック）
    print("警告: HTMLコードブロック(```html...```)が見つかりませんでした。API応答をそのまま返します。", file=sys.stderr)
    return text

# --- メイン処理 ---
def main():
    """メイン関数 (非対話モード)"""
    print("--- AIページブラッシュアップツール (自動モード) ---")

    api_key = get_gemini_api_key()
    if not api_key:
        print("エラー: Gemini APIキーが取得できませんでした。処理を中断します。", file=sys.stderr)
        return
    
    print("-" * 30)

    html_file_path = DEFAULT_HTML_PATH
    if not os.path.exists(html_file_path):
        print(f"エラー: 対象ファイル '{html_file_path}' が見つかりません。", file=sys.stderr)
        print("最初に `generate_ai_homepage.py` を実行してホームページを作成してください。", file=sys.stderr)
        return

    with open(html_file_path, 'r', encoding='utf-8') as f:
        original_html_content = f.read()

    latest_headline = get_latest_rss_headline(NHK_RSS_FEED_URL)
    user_brush_up_instruction = f"今日のニュースのテーマ「{latest_headline}」に合わせて、より魅力的で洗練されたデザインにブラッシュアップしてください。特に、このテーマに関連するコンテンツや表現を強化してください。"
    print(f"AIへのブラッシュアップ指示: {user_brush_up_instruction}")

    brushed_up_html_raw = call_gemini_api_for_brush_up(api_key, original_html_content, user_brush_up_instruction)

    if not brushed_up_html_raw:
        print("エラー: ブラッシュアップコンテンツの生成に失敗しました。", file=sys.stderr)
        return
    
    brushed_up_html = strip_markdown_code_fences(brushed_up_html_raw)

    backup_path = html_file_path + ".bak_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.rename(html_file_path, backup_path)
    print(f"元のファイル '{html_file_path}' を '{backup_path}' にバックアップしました。")

    try:
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(brushed_up_html)
        print(f"\nブラッシュアップされたHTMLが '{html_file_path}' に保存されました。")
    except Exception as e:
        print(f"エラー: ブラッシュアップされたHTMLの保存に失敗しました: {e}", file=sys.stderr)
        return

    print("\n--- 処理完了 ---")

if __name__ == "__main__":
    main()
