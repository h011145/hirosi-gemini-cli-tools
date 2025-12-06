#!/usr/bin/env python3
# DESCRIPTION: ネオワールドサーガ専用の執筆支援AIを起動します。

import time
import sys
import os
import glob
from datetime import datetime
try:
    import google.generativeai as genai # Gemini API Library
except ImportError:
    print("エラー: 'google-generativeai' ライブラリが見つかりません。", file=sys.stderr)
    print("以下のコマンドでインストールしてください:", file=sys.stderr)
    print("pip install google-generativeai", file=sys.stderr)
    sys.exit(1)


# --- パス設定 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_FILE_PATH = os.path.join(PROJECT_ROOT, "api")
NWS_COLLECTION_ROOT = os.path.expanduser("~/neo_world_saga_collection/")


def read_text_file(filepath: str) -> str | None:
    """テキストファイルを読み込み、内容を返す"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"警告: ファイル読み込み中にエラー - {filepath}: {e}", file=sys.stderr)
        return None

def get_gemini_api_key() -> str:
    """APIキーを取得する (apiファイル > 環境変数 > ユーザー入力)"""
    if os.path.exists(API_FILE_PATH):
        with open(API_FILE_PATH, 'r', encoding='utf-8') as f:
            api_key = f.read().strip()
        if api_key:
            return api_key
        else:
            print(f"警告: '{API_FILE_PATH}' は空です。", file=sys.stderr)

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    print("\n--- Gemini APIキーの入力 ---")
    try:
        api_key = input("APIキーを直接入力してください: ")
    except (EOFError, KeyboardInterrupt):
        api_key = ""
    return api_key

def select_lore_files() -> dict:
    """ユーザーに参照するloreファイルを選択させる"""
    print("\n--- 背景資料の選択 ---")
    search_path = os.path.join(NWS_COLLECTION_ROOT, "**", "*.md")
    all_files = sorted(glob.glob(search_path, recursive=True))

    if not all_files:
        print("背景資料となるマークダウンファイルが見つかりませんでした。")
        return {}

    for i, filepath in enumerate(all_files):
        print(f"  [{i+1}] {os.path.relpath(filepath, NWS_COLLECTION_ROOT)}")

    print("\nAIに参照させたいファイルの番号を、カンマ区切りで入力してください。")
    
    try:
        choice = input("(例: 1,3,5) (すべて選択する場合は 'all', 何も選択しない場合はそのままEnter): ")
        if not choice:
            return {}
        if choice.lower() == 'all':
            print("すべてのファイルを選択しました。トークン数上限に注意してください。")
            selected_indices = range(len(all_files))
        else:
            selected_indices = [int(i.strip()) - 1 for i in choice.split(',') if i.strip().isdigit()]
    except (EOFError, KeyboardInterrupt):
        return {}

    lore_data = {}
    print("\n選択されたファイルを読み込み中...")
    for i in selected_indices:
        if 0 <= i < len(all_files):
            filepath = all_files[i]
            filename = os.path.basename(filepath)
            content = read_text_file(filepath)
            if content:
                lore_data[filename] = content
                print(f"  - {filename} を読み込みました。")
    
    return lore_data

def generate_story_with_gemini(api_key: str, lore_data: dict[str, str], user_instruction: str) -> str | None:
    """Gemini APIを呼び出して物語を生成する"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt_parts = [
            "あなたはネオワールドサーガの世界観と文体を深く理解したAIライターです。\n",
            "以下の背景資料に基づき、ユーザーの指示に従って物語を生成してください。\n",
            "物語の文末は、必ず「余韻」を残す形で締めくくってください。明確な結末は必要ありません。\n",
            "====================\n",
            "--- 背景資料 ---\n",
        ]
        if not lore_data:
            prompt_parts.append("（背景資料なし）\n")
        else:
            for filename, content in lore_data.items():
                prompt_parts.append(f"ファイル名: {filename}\n内容:\n{content}\n\n")
        
        prompt_parts.append("====================\n")
        prompt_parts.extend([
            f"--- ユーザーからの執筆指示 ---\n{user_instruction}\n",
            "====================\n",
            "上記情報に基づき、ネオワールドサーガの物語を執筆してください。\n",
        ])

        full_prompt = "".join(prompt_parts)
        
        print("\nGemini APIを呼び出し、物語を生成中...しばらくお待ちください。")
        response = model.generate_content(full_prompt)
        
        return response.text

    except Exception as e:
        print(f"エラー: Gemini APIの呼び出し中にエラーが発生しました: {e}", file=sys.stderr)
        return None

def main():
    """メイン関数"""
    print("ようこそ、ネオワールドサーガ執筆支援エージェントへ。")
    print("-" * 30)

    api_key = get_gemini_api_key()
    if not api_key:
        print("エラー: Gemini APIキーが取得できませんでした。処理を中断します。", file=sys.stderr)
        return
    
    print("-" * 30)
    
    # Loreファイルの選択
    lore_data = select_lore_files()
    if not lore_data:
        print("\n背景資料は選択されませんでした。")
    else:
        print(f"\n{len(lore_data)}個のLoreファイルを選択しました。")

    print("-" * 30)
    
    # ユーザーからのプロット指示の受け付け
    try:
        print("\n--- 物語のプロット指示 ---")
        user_plot_instruction = input("どのような物語を執筆したいですか？ (例: ガトールが新たな敵と出会う場面)\n> ")
        if not user_plot_instruction:
            print("プロット指示が入力されませんでした。処理を中断します。")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n入力がキャンセルされました。処理を中断します。", file=sys.stderr)
        return
        
    print("-" * 30)

    # Gemini APIの呼び出し
    generated_story = generate_story_with_gemini(api_key, lore_data, user_plot_instruction)

    if generated_story:
        print("\n--- 生成された物語 ---")
        print(generated_story)
        print("--------------------")

        # ファイルへの自動保存
        save_dir = os.path.join(NWS_COLLECTION_ROOT, "99_その他")
        os.makedirs(save_dir, exist_ok=True) 

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ファイル名として安全な文字列を生成
        safe_chars = [c if c.isalnum() else '_' for c in user_plot_instruction]
        filename_base = "".join(safe_chars)[:50] or "untitled"
        
        filename = f"generated_story_{timestamp}_{filename_base}.md"
        save_path = os.path.join(save_dir, filename)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"# プロット指示: {user_plot_instruction}\n\n")
                f.write(generated_story)
            print(f"\n物語を以下のファイルに保存しました:\n{save_path}")
        except Exception as e:
            print(f"\nエラー: 物語のファイル保存中にエラーが発生しました: {e}", file=sys.stderr)
    else:
        print("\n物語の生成に失敗しました。", file=sys.stderr)
    
    print("\nスクリプトの全処理が完了しました。")

if __name__ == "__main__":
    main()