#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*- 
# DESCRIPTION:ネオワールドサーガの動画とホームページの生成からデプロイまでをオーケストレーションします。

import os
import sys
import glob
import random
import re
import subprocess
from datetime import datetime

# 外部スクリプトをインポート
# sys.path にスクリプトのディレクトリを追加してインポート可能にする
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# 各モジュールをインポート (main関数が値を返すように修正済みを想定)
import generate_narration_audio
import generate_scene_images
import assemble_video
import generate_ai_homepage # ホームページ生成スクリプト

# --- 定数 ---
NWS_COLLECTION_ROOT = os.path.expanduser("~/neo_world_saga_collection/")
GEMINI_TMP_DIR = os.path.expanduser("~/.gemini/tmp/2a5cc3f9e55f69e8861c4b2400ee9808e005edeef0f96209c1a7cc301661792e") 

# Ensure GEMINI_TMP_DIR exists
os.makedirs(GEMINI_TMP_DIR, exist_ok=True)

# --- ヘルパー関数 ---
def load_random_saga_story() -> tuple[str | None, str | None]:
    """ネオワールドサーガの物語をランダムに選び、内容とファイル名を返す"""
    try:
        search_path = os.path.join(NWS_COLLECTION_ROOT, "**", "*.md")
        files = glob.glob(search_path, recursive=True)
        if not files:
            print(f"警告: ディレクトリに物語ファイルが見つかりません: {NWS_COLLECTION_ROOT}", file=sys.stderr)
            return None, None
        
        selected_file = random.choice(files)
        with open(selected_file, 'r', encoding='utf-8') as f:
            return f.read(), os.path.basename(selected_file)
    except Exception as e:
        print(f"エラー: 物語のランダム読み込み中にエラー: {e}", file=sys.stderr)
        return None, None

# --- メイン処理 ---
def main():
    """
    動画生成パイプラインをオーケストレーションし、生成された動画ファイルのパスを返します。
    """
    print("--- 全体オーケストレーター開始 ---")

    # 1. 物語の選択
    print("\n1. ネオワールドサーガの物語を選択中...")
    story_content, story_name = load_random_saga_story()
    if not story_content:
        print("エラー: 物語を取得できませんでした。処理を中止します。", file=sys.stderr)
        return 1
    print(f"  - 選択された物語: {story_name}")

    audio_filepath = None
    image_filepath = None
    video_filepath = None
    html_filepath = None

    try:
        # 2. ナレーション音声を生成
        print("\n2. ナレーション音声を生成中...")
        audio_filepath = generate_narration_audio.main(story_content, story_name)
        if not audio_filepath:
            print("エラー: ナレーション音声ファイルの生成に失敗しました。", file=sys.stderr)
            return 1
        print(f"  - 生成された音声ファイル: {audio_filepath}")

        # 3. シーン画像を生成
        print("\n3. シーン画像を生成中...")
        image_filepath = generate_scene_images.main(story_content, story_name)
        if not image_filepath:
            print("エラー: シーン画像ファイルの生成に失敗しました。", file=sys.stderr)
            return 1
        print(f"  - 生成された画像ファイル: {image_filepath}")

        # 4. 動画を組み立て
        print("\n4. 動画を組み立て中...")
        video_filepath = assemble_video.main(audio_filepath, image_filepath)
        if not video_filepath:
            print("エラー: 動画ファイルの組み立てに失敗しました。", file=sys.stderr)
            return 1
        print(f"  - 生成された動画ファイル: {video_filepath}")

        # 5. ホームページコンテンツを生成 (動画埋め込み含む)
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

        # check=True は CalledProcessError を送出する
        deploy_process = subprocess.run(deploy_command, capture_output=True, text=True, check=True)
        print("--- デプロイスクリプト STDOUT ---")
        print(deploy_process.stdout)
        if deploy_process.stderr:
            print("--- デプロイスクリプト STDERR ---")
            print(deploy_process.stderr, file=sys.stderr)
        print("デプロイプロセスが完了しました。")

    except subprocess.CalledProcessError as e:
        print("エラー: デプロイスクリプトの実行に失敗しました。", file=sys.stderr)
        print(f"リターンコード: {e.returncode}", file=sys.stderr)
        print("\n--- FAILED SCRIPT STDOUT ---", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print("\n--- FAILED SCRIPT STDERR ---", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"エラー: パイプライン実行中に予期せぬエラーが発生しました: {e}", file=sys.stderr)
        return 1

    
    print("\n--- 全体オーケストレーター完了 ---")
    return 0 # 成功

if __name__ == "__main__":
    sys.exit(main())
