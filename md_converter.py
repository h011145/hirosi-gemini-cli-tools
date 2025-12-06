#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: Markdown原稿を、単一の美しいHTMLファイルに変換します。（一括変換版）

import sys
import os
import glob
import markdown
from datetime import datetime
import re # description生成用
import shutil # クリーンアップ用

# --- 定数 ---
NWS_COLLECTION_ROOT = os.path.expanduser("~/neo_world_saga_collection/")
OUTPUT_DIR = os.path.expanduser("~/neo-world-saga-site/public/")
TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), "template.html") # template.htmlのパス

def load_html_template(template_path: str) -> str:
    """外部のHTMLテンプレートファイルを読み込む"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"エラー: HTMLテンプレートの読み込みに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

# HTMLテンプレートを読み込み
HTML_TEMPLATE = load_html_template(TEMPLATE_FILE)


def generate_description(markdown_text: str) -> str:
    """Generate meta description from Markdown text."""
    plain_text = re.sub(r'\[.*?\]\(.*?\)|\!.\[.*?\]\(.*?\)|\*{1,2}|\_{1,2}|\#{1,6}|`{1,3}.*?`{1,3}|- |\* |> ', '', markdown_text)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    
    description_length = 160
    if len(plain_text) > description_length:
        description = plain_text[:description_length] + "..."
    else:
        description = plain_text
    return description.replace('"', '&quot;')

def process_markdown_file(filepath: str):
    """Processes a Markdown file, converts to HTML, and saves it."""
    try:
        title = os.path.basename(filepath).replace('.md', '').replace('_', ' ')
        print(f"--- 変換開始: {title} ---")

        # Markdownファイル読み込み
        with open(filepath, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        # descriptionを生成
        description = generate_description(markdown_text)

        # 3. HTMLに変換
        print("HTMLに変換中...")
        html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])

        # 4. テンプレートに埋め込み
        final_html = HTML_TEMPLATE.format(title=title, description=description, content=html_content)

        # 5. HTMLファイルとして保存
        output_filename = os.path.basename(filepath).replace('.md', '.html')
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"変換完了！出力ファイル: {output_filepath}")
        return True

    except Exception as e:
        print(f"エラー: {filepath} の変換中に失敗しました: {e}", file=sys.stderr)
        return False

def main():
    """Main function to perform batch conversion of Markdown files to HTML."""
    print("--- Markdown to HTML コンバーター（一括変換） ---")
    print(f"対象ディレクトリ: {NWS_COLLECTION_ROOT}")
    print(f"出力ディレクトリ: {OUTPUT_DIR}")
    print("----------------------------------------")

    # 出力ディレクトリのクリーンアップ
    print(f"出力ディレクトリ {OUTPUT_DIR} をクリーンアップします...")
    if os.path.exists(OUTPUT_DIR):
        # .gitディレクトリを残して他のファイルを削除
        for item in os.listdir(OUTPUT_DIR):
            item_path = os.path.join(OUTPUT_DIR, item)
            if item != ".git": # .gitディレクトリは削除しない
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
    os.makedirs(OUTPUT_DIR, exist_ok=True) # 出力ディレクトリを確実に作成
    print("クリーンアップ完了。")
    print("----------------------------------------")

    # 全てのMarkdownファイルを検索
    all_md_files = []
    try:
        for root, _, files in os.walk(NWS_COLLECTION_ROOT):
            for name in files:
                if name.endswith(".md"):
                    all_md_files.append(os.path.join(root, name))
        all_md_files.sort()
    except Exception as e:
        print(f"ファイル検索中にエラーが発生しました: {e}", file=sys.stderr)
        return

    if not all_md_files:
        print(f"エラー: {NWS_COLLECTION_ROOT} 以下に .md ファイルが見つかりませんでした。")
        return

    print(f"{len(all_md_files)} 個のMarkdownファイルを検出しました。変換を開始します。\n")

    successful_conversions = 0
    for md_file_path in all_md_files:
        if process_markdown_file(md_file_path):
            successful_conversions += 1
        print("----------------------------------------")

    print(f"\n--- 処理完了 ---")
    print(f"成功: {successful_conversions} 個, 失敗: {len(all_md_files) - successful_conversions} 個")
    print(f"変換されたHTMLファイルは {OUTPUT_DIR} に出力されました。")

if __name__ == "__main__":
    main()
