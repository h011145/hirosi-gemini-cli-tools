#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION:ネオワールドサーガの物語からOpen JTalkを使ってナレーション音声を生成します。

import os
import sys
import subprocess
import glob
import random
import re
from datetime import datetime
import markdown
from bs4 import BeautifulSoup

# --- 定数 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NWS_COLLECTION_ROOT = os.path.expanduser("~/neo_world_saga_collection/")
AUDIO_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "scripts", "generated_audio")

# Open JTalkのパス設定
OPEN_JTALK_DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
OPEN_JTALK_VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"

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

def clean_text_for_tts(text: str) -> str:
    """音声合成のためにMarkdownからクリーンなテキストを抽出し、改行を句読点に変換する。"""
    html_content = markdown.markdown(text, extensions=['fenced_code', 'tables'])
    soup = BeautifulSoup(html_content, 'html.parser')
    plain_text = soup.get_text()

    # 複数の改行を一つにまとめる
    plain_text = re.sub(r'\n\s*\n', '\n', plain_text).strip()
    # 残った改行を読点に変換し、自然な間を表現
    plain_text = plain_text.replace('\n', '、')
    # 複数のスペースを一つに
    plain_text = re.sub(r' +', ' ', plain_text)

    return plain_text

# --- Open JTalk実行関数 ---
def generate_audio_from_text(text: str, output_filepath: str) -> bool:
    """テキストからOpen JTalkを使って音声ファイルを生成する"""
    print(f"音声ファイルを生成中: {output_filepath}")

    command = [
        'open_jtalk',
        '-x', OPEN_JTALK_DIC,
        '-m', OPEN_JTALK_VOICE,
        '-ow', output_filepath
    ]

    try:
        subprocess.run(command, input=text, text=True, check=True, capture_output=True, encoding='utf-8')
        print("音声ファイルの生成が完了しました。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"エラー: Open JTalkの実行に失敗しました。", file=sys.stderr)
        print(f"エラー出力:\n{e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"エラー: 'open_jtalk' コマンドが見つかりません。インストールされているか確認してください。", file=sys.stderr)
        return False

# --- メイン処理 ---
def main(input_story_content: str = None, input_story_name: str = None) -> str | None:
    """メイン関数"""
    print("--- ナレーション音声生成ツール ---")

    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

    if not (input_story_content and input_story_name):
        print("エラー: 物語のコンテンツと名前が必要です。", file=sys.stderr)
        return None

    # 引数をローカル変数に割り当てる
    story_content = input_story_content
    story_name = input_story_name

    print(f"物語テーマ (引数から): {story_name}")

    cleaned_story = clean_text_for_tts(story_content)
    if not cleaned_story.strip():
        print("エラー: 音声合成するテキスト内容がありません。", file=sys.stderr)
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_story_name = re.sub(r'[^\w\-_\. ]', '_', story_name.replace('.md', ''))
    output_filename = f"narration_{safe_story_name}_{timestamp}.wav"
    output_filepath = os.path.join(AUDIO_OUTPUT_DIR, output_filename)
    
    if not generate_audio_from_text(cleaned_story, output_filepath):
        return None

    print(f"\n生成されたファイル: {output_filepath}")
    print("--- 全処理完了 ---")
    return output_filepath


if __name__ == "__main__":
    if len(sys.argv) == 3:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                content = f.read()
            # mainの戻り値でexitコードを決定
            if main(content, sys.argv[2]):
                sys.exit(0)
            else:
                sys.exit(1)
        except Exception as e:
            print(f"エラー: コマンドライン引数からの物語読み込み中にエラー: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("使用法: python generate_narration_audio.py <story_filepath> <story_name>", file=sys.stderr)
        sys.exit(1)