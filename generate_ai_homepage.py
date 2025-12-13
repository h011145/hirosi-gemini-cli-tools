#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: Gemini APIを利用してAIビジネスのホームページコンテンツを生成し、HTMLファイルとして保存します。

import os
import sys
import json
import datetime

# Gemini API ライブラリをインポート
try:
    import google.generativeai as genai
except ImportError:
    print("エラー: 'google-generativeai' ライブラリが見つかりません。", file=sys.stderr)
    print("以下のコマンドでインストールしてください:", file=sys.stderr)
    print("pip install google-generativeai", file=sys.stderr)
    sys.exit(1)


# --- パス設定 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_FILE_PATH = os.path.join(PROJECT_ROOT, "api")
OUTPUT_DIR_PUBLIC = "/var/www/html/public/" # 出力ディレクトリは固定

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

# Gemini API の呼び出し (現在はモックではなく実APIを呼び出す)
def call_gemini_api(api_key: str, prompt_text: str, site_name: str) -> str:
    print("\n--- Gemini APIにコンテンツ生成をリクエスト中 ---")
    print("プロンプト:\n", prompt_text[:500] + "..." if len(prompt_text) > 500 else prompt_text)
    
    try:
        genai.configure(api_key=api_key)
        # モデルを gemini-2.5-flash に変更
        model = genai.GenerativeModel('gemini-2.5-flash')

        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        print(f"エラー: Gemini APIの呼び出し中にエラーが発生しました: {e}", file=sys.stderr)
        return ""

def get_user_input(prompt_text: str, default_value: str = "") -> str:
    """ユーザーからの入力を取得するヘルパー関数"""
    return input(f"{prompt_text} [{default_value}]: ") or default_value

def main():
    """メイン関数"""
    print("--- AIビジネスホームページコンテンツ生成ツール ---")

    api_key = get_gemini_api_key()
    if not api_key:
        print("エラー: Gemini APIキーが取得できませんでした。処理を中断します。", file=sys.stderr)
        return
    
    print("-" * 30)

    # ユーザーからビジネス情報を取得
    business_purpose = get_user_input("ビジネスの目的 (例: 革新的なAIソリューションの提供)", "革新的なAIソリューションの提供")
    target_customers = get_user_input("ターゲット顧客 (例: 中小企業、スタートアップ)", "中小企業、スタートアップ")
    services_offered = get_user_input("提供するサービス (例: コンテンツ自動生成、データ分析)", "コンテンツ自動生成、データ分析")
    contact_info = get_user_input("連絡先情報 (例: info@example.com, Twitter: @example_ai)", "info@example.com")
    site_name = get_user_input("ホームページのタイトル (例: AI Business Solutions)", "AI Business Solutions")


    # プロンプトを構築
    prompt = f"""
あなたは、AIビジネスのホームページのコンテンツとHTML構造を生成する専門家です。以下の情報に基づき、コンテンツとHTML骨子（bodyタグ内）を作成してください。

**デザイン要件:**
*   堅牢でシックな雰囲気にしてください。
*   画像は直接埋め込まず、視覚情報は動画サイトへのリンク（埋め込みコードではない）で表現してください。
*   上記要件以外で、HTMLやスタイルで表現可能な部分は、積極的に活用し、効果的に色（CSSの `color` や `background-color` など）も使用して、魅力的で分かりやすいコンテンツにしてください。

**ビジネス情報:**
*   **ビジネスの目的:** {business_purpose}
*   **ターゲット顧客:** {target_customers}
*   **提供するサービス:** {services_offered}
*   **連絡先:** {contact_info}

**生成する内容:**
*   メインタイトルとサブタイトル
*   ビジネスの紹介文
*   サービス内容の詳細（各サービスの簡単な説明）
*   お客様の声（架空で可）
*   行動喚起（CTA）
*   フッター情報
*   動画サイトへのリンク（例: YouTube動画へのリンクを数カ所）

**出力形式:**
*   HTMLの`<body>`タグ内のみを生成してください。
*   CSSやJavaScriptは含めないでください。
*   HTML要素は意味論的に正しいものを使用し、Bootstrapなどのフレームワークは考慮せず、プレーンなHTML構造でお願いします。
"""

    # Gemini API を呼び出し
    generated_body_html = call_gemini_api(api_key, prompt, site_name)

    if not generated_body_html:
        print("エラー: コンテンツの生成に失敗しました。", file=sys.stderr)
        return

    # 最終的なHTMLファイルテンプレート
    full_html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_title}</title>
    <!-- プロジェクトサイトのCSS/JS/画像への正しいパス解決のためにBASEタグを追加 -->
    <base href="https://h011145.github.io/ai-business-homepage-experiment/">
</head>
<body>
{body_content}
</body>
</html>"""

    # 最終的なHTMLファイルを構築
    full_html_content = full_html_template.format(site_title=site_name, body_content=generated_body_html)

    # ファイル名を決定
    output_filename = "ai_business_homepage.html"
    output_filepath = os.path.join(OUTPUT_DIR_PUBLIC, output_filename)

    # HTMLファイルを保存
    os.makedirs(OUTPUT_DIR_PUBLIC, exist_ok=True) # 出力ディレクトリを確実に作成
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(full_html_content)
        print(f"\nホームページコンテンツが {output_filepath} に生成されました。")
    except Exception as e:
        print(f"エラー: ホームページコンテンツの保存に失敗しました: {e}", file=sys.stderr)
        return

    print("\n--- 処理完了 ---")

if __name__ == "__main__":
    main()
