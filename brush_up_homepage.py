#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: 既存のHTMLファイルをGemini APIでブラッシュアップします。

import os
import sys
import json
from bs4 import BeautifulSoup

# Gemini API ライブラリをインポート
try:
    import google.generativeai as genai
except ImportError:
    print("エラー: 'google-generativeai' ライブラリが見つかりません。", file=sys.stderr)
    print("以下のコマンドでインストールしてください:", file=sys.stderr)
    print("pip install google-generativeai", file=sys.stderr)
    sys.exit(1)


# --- パス設定 (generate_ai_homepage.py と共通) ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_FILE_PATH = os.path.join(PROJECT_ROOT, "api")
DEFAULT_HTML_PATH = "/var/www/html/public/ai_business_homepage.html"


# --- APIキー取得関数 (nws_writer.py から移植) ---
def get_gemini_api_key() -> str:
    """APIキーを取得する (apiファイル > 環境変数 > ユーザー入力)"""
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
    
    # ユーザー入力を求めるのは一度だけ
    if not hasattr(get_gemini_api_key, 'asked_for_input'):
        print("\n--- Gemini APIキーの入力 ---")
        try:
            api_key = input("APIキーを直接入力してください: ")
            get_gemini_api_key.asked_for_input = True # 入力を求めたフラグ
        except (EOFError, KeyboardInterrupt):
            api_key = ""
        return api_key
    else:
        return "" # 既に入力を求めた場合は空を返す


# Gemini API の呼び出し
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
        
        print("プロンプト:\n", full_prompt[:1000] + "..." if len(full_prompt) > 1000 else full_prompt)
        print("--- Gemini API呼び出し中...しばらくお待ちください。 ---")
        
        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        print(f"エラー: Gemini APIの呼び出し中にエラーが発生しました: {e}", file=sys.stderr)
        return ""

def strip_markdown_code_fences(text: str) -> str:
    """Gemini APIの応答からMarkdownのコードブロックを示す ```html や ``` を削除する"""
    # 冒頭の ```html を削除
    if text.startswith('```html'):
        text = text[len('```html'):].strip()
    # 末尾の ``` を削除
    if text.endswith('```'):
        text = text[:-len('```')].strip()
    return text

def get_user_input(prompt_text: str, default_value: str = "") -> str:
    """ユーザーからの入力を取得するヘルパー関数"""
    return input(f"{prompt_text} [{default_value}]: ") or default_value

def main():
    """メイン関数"""
    print("--- AIページブラッシュアップツール ---")

    api_key = get_gemini_api_key()
    if not api_key:
        print("エラー: Gemini APIキーが取得できませんでした。処理を中断します。", file=sys.stderr)
        return
    
    print("-" * 30)

    # ブラッシュアップ対象のHTMLファイルパスを取得
    html_file_path = get_user_input(f"ブラッシュアップするHTMLファイルのパスを入力してください", DEFAULT_HTML_PATH)
    if not os.path.exists(html_file_path):
        print(f"エラー: 指定されたファイル '{html_file_path}' が見つかりません。")
        return

    # 既存のHTMLコンテンツを読み込み
    with open(html_file_path, 'r', encoding='utf-8') as f:
        original_html_content = f.read()

    # ユーザーからのブラッシュアップ指示を取得
    user_brush_up_instruction = get_user_input("どのようにブラッシュアップしたいですか？ (例: テキストをもっと簡潔に、レイアウトを改善など)", "全体的に洗練されたデザインにする")

    # Gemini APIを呼び出し
    brushed_up_html_raw = call_gemini_api_for_brush_up(api_key, original_html_content, user_brush_up_instruction)

    if not brushed_up_html_raw:
        print("エラー: ブラッシュアップコンテンツの生成に失敗しました。", file=sys.stderr)
        return
    
    # Markdownコードブロック記号を削除
    brushed_up_html = strip_markdown_code_fences(brushed_up_html_raw)

    # 既存のファイルをバックアップ
    backup_path = html_file_path + ".bak_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.rename(html_file_path, backup_path)
    print(f"元のファイル '{html_file_path}' を '{backup_path}' にバックアップしました。")

    # 新しいHTMLを元のファイル名で保存
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
