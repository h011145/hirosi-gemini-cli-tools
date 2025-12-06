#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*- 
# DESCRIPTION: 複数のMarkdown原稿を結合し、一つの美しいHTMLファイルに変換します。

import sys
import os
import glob
import markdown
from datetime import datetime
import re # description生成用

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
    """Markdownテキストからmeta descriptionを生成する"""
    plain_text = re.sub(r'\[.*?\]\(.*?\)|!\s*\[.*?\]\(.*?\)|\*{1,2}|\_{1,2}|\#{1,6}|`{1,3}.*?`{1,3}|- |\* |> ', '', markdown_text)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    
    description_length = 160
    if len(plain_text) > description_length:
        description = plain_text[:description_length] + "..."
    else:
        description = plain_text
    return description.replace('"', '&quot;')

def select_multiple_markdown_files() -> list[str]:
    """ユーザーに複数のMarkdownファイルを選択させる"""
    print("\n--- 結合する原稿の選択 ---")
    
    all_md_files = []
    try:
        for root, _, files in os.walk(NWS_COLLECTION_ROOT):
            for name in files:
                if name.endswith(".md"):
                    all_md_files.append(os.path.join(root, name))
        all_md_files.sort()
    except Exception as e:
        print(f"ファイル検索中にエラーが発生しました: {e}", file=sys.stderr)
        return []

    if not all_md_files:
        print(f"エラー: {NWS_COLLECTION_ROOT} 以下に .md ファイルが見つかりませんでした。")
        return []

    for i, filepath in enumerate(all_md_files):
        display_path = filepath.replace(os.path.expanduser('~'), '~', 1)
        print(f"  [{i+1}] {display_path}")
    print("----------------------------------------")

    try:
        choice_str = input("番号をカンマ区切りで入力してください (例: 1,3,5): ")
        if not choice_str.strip():
            return []
        
        selected_files = []
        chosen_indices = [int(x.strip()) - 1 for x in choice_str.split(',') if x.strip().isdigit()]
        
        for index in chosen_indices:
            if 0 <= index < len(all_md_files):
                selected_files.append(all_md_files[index])
            else:
                print(f"警告: 無効な番号 '{index + 1}' はスキップされます。", file=sys.stderr)
        
        return selected_files

    except (EOFError, KeyboardInterrupt):
        return []
    except ValueError:
        print("エラー: 入力形式が正しくありません。番号をカンマ区切りで入力してください。", file=sys.stderr)
        return []

def main():
    """メイン関数"""
    print("--- 章まとめコンバーター ---")
    print(f"対象ディレクトリ: {NWS_COLLECTION_ROOT}")
    print(f"出力ディレクトリ: {OUTPUT_DIR}")
    print("----------------------------------------")

    # 1. ファイル選択
    selected_md_files = select_multiple_markdown_files()
    if not selected_md_files:
        print("\nファイルが選択されませんでした。処理を中断します。")
        return

    print("\n選択されたファイル:")
    for f in selected_md_files:
        print(f"  - {f}")
    
    # 2. 結合されたタイトルを決定
    combined_title_parts = [os.path.basename(f).replace('.md', '').replace('_', ' ') for f in selected_md_files]
    combined_title = " ".join(combined_title_parts[:3]) # 最初の3つを結合
    if len(combined_title_parts) > 3:
        combined_title += " など"
    combined_title = f"結合された章: {combined_title}"
    
    print(f"\n生成されるHTMLのタイトル: {combined_title}")

    # 3. Markdownコンテンツを結合
    combined_markdown_text = ""
    for md_file_path in selected_md_files:
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                combined_markdown_text += f.read() + "\n\n" # 各章の間に改行を追加
        except Exception as e:
            print(f"エラー: {md_file_path} の読み込みに失敗しました: {e}", file=sys.stderr)
            return
    
    # descriptionを生成
    description = generate_description(combined_markdown_text)

    # 4. HTMLに変換
    print("HTMLに変換中...")
    html_content = markdown.markdown(combined_markdown_text, extensions=['fenced_code', 'tables'])

    # 5. テンプレートに埋め込み
    final_html = HTML_TEMPLATE.format(title=combined_title, description=description, content=html_content)

    # 6. HTMLファイルとして保存
    os.makedirs(OUTPUT_DIR, exist_ok=True) # 出力ディレクトリを確実に作成

    # 出力ファイル名はスラッグ化されたタイトルを使用
    output_filename_base = combined_title.replace(' ', '_').replace(':', '') # タイトルから安全なファイル名を作成
    output_filename = f"{output_filename_base}.html"
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print("\n変換が完了しました！")
        print(f"出力ファイル: {output_filepath}")
    except Exception as e:
        print(f"エラー: HTMLファイルの保存に失敗しました: {e}", file=sys.stderr)
        return

    print("\n--- 処理完了 ---")

if __name__ == "__main__":
    main()
