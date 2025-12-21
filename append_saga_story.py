#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*- 
# DESCRIPTION:ネオワールドサーガの物語をランダムに一つ選び、その続きをAIに執筆させてファイルに追記します。

import os
import sys
import random
import glob
import time

try:
    import google.generativeai as genai
except ImportError:
    print("エラー: 'google-generativeai' ライブラリが見つかりません。", file=sys.stderr)
    sys.exit(1)

# --- 定数 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_FILE_PATH = os.path.join(PROJECT_ROOT, "api")
NWS_COLLECTION_ROOT = os.path.expanduser("~/neo_world_saga_collection/")

# --- APIキー取得 ---
def get_gemini_api_key() -> str | None:
    if os.path.exists(API_FILE_PATH):
        with open(API_FILE_PATH, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return os.getenv("GEMINI_API_KEY")

# --- メイン処理 ---
def main():
    """物語の続きを自動執筆するメイン関数"""
    print("--- ネオワールドサーガ 自動執筆開始 ---")

    # 1. APIキーの確認
    api_key = get_gemini_api_key()
    if not api_key:
        print("エラー: Gemini APIキーが取得できませんでした。", file=sys.stderr)
        return False

    # 2. 執筆対象の物語をランダムに選択
    try:
        search_path = os.path.join(NWS_COLLECTION_ROOT, "**", "*.md")
        files = glob.glob(search_path, recursive=True)
        if not files:
            print(f"警告: ディレクトリに物語ファイルが見つかりません: {NWS_COLLECTION_ROOT}", file=sys.stderr)
            return False
        
        selected_file = random.choice(files)
        print(f"執筆対象の物語: {os.path.basename(selected_file)}")

        with open(selected_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

    except Exception as e:
        print(f"エラー: 物語ファイルの読み込み中にエラー: {e}", file=sys.stderr)
        return False

    # 3. AIへの指示プロンプトを構築
    prompt = f"""
あなたは卓越したSF作家であり、既存の物語の続きを執筆する専門家です。
以下の「既存の物語」を読み、その文体、登場人物の口調、物語の雰囲気を完全に維持したまま、自然で魅力的な「続きの物語」を執筆してください。

# 指示
- これまでの物語の流れを壊さないように、ごく自然な続きを執筆してください。
- 出力は「続きの物語」の文章本体のみとし、余計な前置きや後書き（「はい、承知いたしました。続きを執筆します。」など）は一切含めないでください。
- 新しい展開を少しだけ加えて、物語を前に進めてください。

# 既存の物語
{original_content}

# 出力（続きの物語）
"""

    # 4. Gemini APIを呼び出して続きを生成
    print("AIが物語の続きを執筆中...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        new_content = response.text
    except Exception as e:
        print(f"エラー: Gemini APIの呼び出し中にエラー: {e}", file=sys.stderr)
        return False

    if not new_content.strip():
        print("警告: AIが空のコンテンツを生成しました。ファイルへの追記をスキップします。", file=sys.stderr)
        return True # 失敗ではないのでTrue

    # 5. 元のファイルに生成された続きを追記
    print("生成された物語をファイルに追記中...")
    try:
        with open(selected_file, 'a', encoding='utf-8') as f:
            # 元のファイルの末尾が改行で終わっていることを確認し、適切にスペースを空ける
            if not original_content.endswith('\n'):
                f.write('\n')
            f.write('\n\n---\n\n') # 新しいセクションとして区切り線を入れる
            f.write(new_content)
    except Exception as e:
        print(f"エラー: ファイルへの追記中にエラー: {e}", file=sys.stderr)
        return False
    
    print(f"'{os.path.basename(selected_file)}' の執筆が完了しました。")
    print("--- ネオワールドサーガ 自動執筆完了 ---")
    return True


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
