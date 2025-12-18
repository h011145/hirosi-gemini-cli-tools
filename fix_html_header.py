#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DESCRIPTION: ai_business_homepage.htmlから、Gemini APIの応答に含まれるヘッダーの解説文を削除します。

import os
import sys

TARGET_FILE_PATH = "/var/www/html/public/ai_business_homepage.html"

def fix_html_file():
    """
    対象のHTMLファイルを読み込み、'<!DOCTYPE html>'以前の不要なテキストを削除して上書きします。
    """
    print(f"--- HTMLヘッダー修正スクリプト開始 ---")
    print(f"対象ファイル: {TARGET_FILE_PATH}")

    if not os.path.exists(TARGET_FILE_PATH):
        print(f"エラー: 対象ファイルが見つかりません: {TARGET_FILE_PATH}", file=sys.stderr)
        return

    try:
        with open(TARGET_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"エラー: ファイルの読み込みに失敗しました: {e}", file=sys.stderr)
        return

    # 'DOCTYPE'宣言を探す (大文字・小文字を区別しない)
    doctype_marker = '<!DOCTYPE html>'
    index = content.lower().find(doctype_marker.lower())

    if index == -1:
        print(f"エラー: ファイル内に '{doctype_marker}' が見つかりませんでした。修正を中止します。", file=sys.stderr)
        return

    # DOCTYPE宣言以降のコンテンツを取得
    cleaned_content = content[index:]

    # ファイルを上書き保存
    try:
        with open(TARGET_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        print("ファイルの修正が完了しました。不要なヘッダー部分が削除されました。")
    except Exception as e:
        print(f"エラー: ファイルの上書き保存に失敗しました: {e}", file=sys.stderr)
        return
        
    print("--- 処理完了 ---")

if __name__ == "__main__":
    fix_html_file()
