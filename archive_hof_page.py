#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DESCRIPTION: 殿堂入りしたホームページをアーカイブします。

import os
import sys
import shutil
from datetime import datetime

SOURCE_FILE = "/var/www/html/public/ai_business_homepage.html"
DEST_DIR = os.path.expanduser("~/neo_world_saga_collection/hall_of_fame_pages/")

def archive_file():
    """
    ソースファイルを日付付きのファイル名で目的のディレクトリにコピーします。
    """
    print("--- 殿堂入りページアーカイブスクリプト開始 ---")
    
    if not os.path.exists(SOURCE_FILE):
        print(f"エラー: コピー元のファイルが見つかりません: {SOURCE_FILE}", file=sys.stderr)
        return

    if not os.path.isdir(DEST_DIR):
        print(f"エラー: 保存先ディレクトリが見つかりません: {DEST_DIR}", file=sys.stderr)
        return

    # 新しいファイル名を生成 (例: hof_page_20251216_083015.html)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S") # 修正: 時分秒を追加
    dest_filename = f"hof_page_{date_str}.html"
    dest_path = os.path.join(DEST_DIR, dest_filename)

    print(f"コピー元: {SOURCE_FILE}")
    print(f"コピー先: {dest_path}")

    try:
        shutil.copy2(SOURCE_FILE, dest_path) # copy2はメタデータも保持しようとする
        print("ファイルのコピーが完了しました。")
    except Exception as e:
        print(f"エラー: ファイルのコピー中にエラーが発生しました: {e}", file=sys.stderr)
        return
        
    print("--- 処理完了 ---")

if __name__ == "__main__":
    archive_file()