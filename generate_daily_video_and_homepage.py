#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION:ネオワールドサーガの物語を自動執筆し、動画とホームページの生成からデプロイまでをオーケストレーションします。

import os
import sys
import glob
import random
import re
import subprocess
from datetime import datetime

# 外部スクリプトをインポート
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# 各モジュールをインポート
import append_saga_story
import assemble_video # ImageMagick/ffmpeg版
import generate_ai_homepage

# --- 定数 ---
NWS_COLLECTION_ROOT = os.path.expanduser("~/neo_world_saga_collection/")
BGM_FILEPATH = "/usr/share/starfighter/music/frozen_jam.ogg"

# --- ヘルパー関数 ---
def load_random_saga_story() -> tuple[str | None, str | None]:
    """ネオワールドサーガの物語をランダムに選び、内容とファイル名を返す"""
    try:
        search_path = os.path.join(NWS_COLLECTION_ROOT, "**", "*.md")
        files = glob.glob(search_path, recursive=True)
        if not files:
            print(f"警告: ディレクトリに物語ファイルが見つかりません: {NWS_COLLECTION_ROOT}", file=sys.stderr)
            return None, None
        
        valid_files = [f for f in files if os.path.getsize(f) > 200]
        if not valid_files:
            print(f"警告: 200バイト以上の物語ファイルが見つかりません。", file=sys.stderr)
            return None, None

        selected_file = random.choice(valid_files)
        with open(selected_file, 'r', encoding='utf-8') as f:
            return f.read(), os.path.basename(selected_file)
    except Exception as e:
        print(f"エラー: 物語のランダム読み込み中にエラー: {e}", file=sys.stderr)
        return None, None

# --- メイン処理 ---
def main():
    """動画生成パイプラインをオーケストレーションします。"""
    print("--- 全体オーケストレーター開始 ---")

    try:
        # 1. 物語の続きを自動執筆
        print("\n1. ネオワールドサーガの物語を自動執筆中...")
        if not append_saga_story.main():
            # このステップは失敗しても致命的ではないため、警告に留めて続行
            print("警告: 物語の自動執筆に失敗しました。処理は続行します。", file=sys.stderr)
        
        # 2. 動画・HP化する物語をランダムに選択
        print("\n2. 動画・ホームページ化する物語を選択中...")
        story_content, story_name = load_random_saga_story()
        if not story_content:
            print("エラー: 物語を取得できませんでした。処理を中止します。", file=sys.stderr)
            return 1
        print(f"  - 選択された物語: {story_name}")

        # 変数初期化
        video_filepath = None
        html_filepath = None
        audio_filepath = BGM_FILEPATH

        # 3. ナレーション音声を生成（今回はスキップ）
        print("\n3. ナレーション音声をスキップし、BGMを使用します。")

        # 4. テキストと映像を合成
        print("\n4. 動画を組み立て中 (ImageMagick/ffmpeg版)...")
        video_filepath = assemble_video.main(story_content, story_name, audio_filepath)
        if not video_filepath:
            print("エラー: 動画ファイルの組み立てに失敗しました。", file=sys.stderr)
            return 1
        print(f"  - 生成された動画ファイル: {video_filepath}")

        # 5. ホームページコンテンツを生成
        print("\n5. ホームページコンテンツを生成中 (動画埋め込み)...")
        html_filepath = generate_ai_homepage.main(story_content, story_name, video_filepath)
        if not html_filepath:
            print("エラー: ホームページコンテンツの生成に失敗しました。", file=sys.stderr)
            return 1
        print(f"  - 生成されたHTMLファイル: {html_filepath}")

        # 6. デプロイ
        print("\n6. ホームページと動画をデプロイ中...")
        deploy_script_path = os.path.join(script_dir, "deploy_ai_business_homepage.sh")
        deploy_command = [deploy_script_path, video_filepath]

        deploy_process = subprocess.run(deploy_command, capture_output=True, text=True, check=True)
        print("--- デプロイスクリプト STDOUT ---")
        print(deploy_process.stdout)
        if deploy_process.stderr:
            print("--- デプロイスクリプト STDERR ---", file=sys.stderr)
            print(deploy_process.stderr, file=sys.stderr)
        print("デプロイプロセスが完了しました。")

    except subprocess.CalledProcessError as e:
        print("エラー: スクリプトの実行に失敗しました。", file=sys.stderr)
        print(f"リターンコード: {e.returncode}", file=sys.stderr)
        print("\n--- FAILED SCRIPT STDOUT ---", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print("\n--- FAILED SCRIPT STDERR ---", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return 1
    except Exception as e:
        import traceback
        print(f"エラー: パイプライン実行中に予期せぬエラーが発生しました: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1

    print("\n--- 全体オーケストレーター完了 ---")
    return 0 # 成功

if __name__ == "__main__":
    sys.exit(main())