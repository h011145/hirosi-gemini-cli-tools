#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*- 
# DESCRIPTION: neo_world_saga_collectionの全Markdownを結合し、master saga HTMLを生成します。

import sys
import os
import glob
import markdown
from datetime import datetime
import re # description生成用
import shutil # クリーンアップ用

# --- 定数 ---
NWS_COLLECTION_ROOT = os.path.expanduser("~/neo_world_saga_collection/")
OUTPUT_FILE_PATH = os.path.join(os.path.expanduser("/var/www/html/public/"), "neo_world_saga.html")
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
    """Markdownテキストからmeta descriptionを生成する"""
    plain_text = re.sub(r'\[.*?\]\(.*?\)|\!.\[.*?\]\(.*?\)|\*{1,2}|\_{1,2}|\#{1,6}|`{1,3}.*?`{1,3}|- |\* |> ', '', markdown_text)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    
    description_length = 160
    if len(plain_text) > description_length:
        description = plain_text[:description_length] + "..."
    else:
        description = plain_text
    return description.replace('"', '&quot;')

def main():
    """メイン関数"""
    print("--- マスターサーガ HTML生成ツール ---")
    print(f"対象コレクション: {NWS_COLLECTION_ROOT}")
    print(f"出力ファイル: {OUTPUT_FILE_PATH}")
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

    print(f"{len(all_md_files)} 個のMarkdownファイルを結合してHTMLを生成します。\n")

    combined_markdown_text = ""
    for md_file_path in all_md_files:
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                combined_markdown_text += f"# {os.path.basename(md_file_path).replace('.md', '').replace('_', ' ')}\n\n" # 各ファイルのタイトルを追加
                combined_markdown_text += f.read() + "\n\n---\n\n" # 各章の間に区切りを追加
        except Exception as e:
            print(f"エラー: {md_file_path} の読み込みに失敗しました: {e}", file=sys.stderr)
            return
    
    # メインのタイトル
    main_title = "ネオワールドサーガ マスターコレクション"
    
    # descriptionを生成
    description = generate_description(combined_markdown_text)

    # HTMLに変換
    print("結合されたMarkdownをHTMLに変換中...")
    html_content = markdown.markdown(combined_markdown_text, extensions=['fenced_code', 'tables'])

    # テンプレートに埋め込み
    final_html = HTML_TEMPLATE.format(title=main_title, description=description, content=html_content)

    # HTMLファイルとして保存
    output_dir = os.path.dirname(OUTPUT_FILE_PATH)
    os.makedirs(output_dir, exist_ok=True) # 出力ディレクトリを確実に作成

    try:
        with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print("\n変換が完了しました！")
        print(f"出力ファイル: {OUTPUT_FILE_PATH}")
    except Exception as e:
        print(f"エラー: HTMLファイルの保存に失敗しました: {e}", file=sys.stderr)
        return

    print("\n--- 処理完了 ---")

if __name__ == "__main__":
    main()
