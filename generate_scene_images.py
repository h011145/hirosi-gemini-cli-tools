#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: 物語のテキストからImageMagickを使ってシーン画像を生成します。

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
IMAGE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "scripts", "generated_images")

# ImageMagickのフォント設定 (要調整。システムにインストールされているフォント名を使用)
# 日本語フォント例: 'Noto-Sans-JP', 'TakaoPGothic', 'IPAPGothic' など
FONT = "Noto-Sans-JP" # システムにインストールされているフォント名

# --- ヘルパー関数 ---
def clean_text_for_image(text: str, max_length: int = 100) -> str:
    """画像生成のためにMarkdownからクリーンなテキストを抽出・要約する"""
    html_content = markdown.markdown(text, extensions=['fenced_code', 'tables'])
    soup = BeautifulSoup(html_content, 'html.parser')
    plain_text = soup.get_text()
    plain_text = re.sub(r'\n\s*\n', '\n', plain_text).strip()
    plain_text = re.sub(r' +', ' ', plain_text)

    if len(plain_text) > max_length:
        plain_text = plain_text[:max_length].rsplit(' ', 1)[0] + '...' if ' ' in plain_text[:max_length] else plain_text[:max_length] + '...'
    
    return plain_text or "物語の要約"

def generate_image_from_text(text: str, output_filepath: str, width=1280, height=720) -> bool:
    """ImageMagickを使ってテキストから画像を生成する。成功すればTrue、失敗すればFalseを返す。"""
    print(f"画像を生成中: {output_filepath}")

    command = [
        'convert',
        '-size', f'{width}x{height}',
        'xc:black',
        '-fill', 'white',
        '-gravity', 'center',
        '-pointsize', '40',
        '-interline-spacing', '15',
    ]

    # フォントが指定されていればコマンドに追加
    if FONT:
        command.extend(['-font', FONT])

    command.extend(['-annotate', '0', text, output_filepath])

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print("画像の生成が完了しました。")
        if not os.path.exists(output_filepath):
             print(f"エラー: 画像生成は成功しましたが、ファイルが見つかりません: {output_filepath}", file=sys.stderr)
             return False
        return True
    except FileNotFoundError:
        print("エラー: 'convert' コマンドが見つかりません。ImageMagickがインストールされているか確認してください。", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print("エラー: ImageMagickの実行に失敗しました。", file=sys.stderr)
        print(f"コマンド: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"リターンコード: {e.returncode}", file=sys.stderr)
        print(f"エラー出力:\n{e.stderr}", file=sys.stderr)
        return False

# --- メイン処理 ---
def main(input_story_content: str = None, input_story_name: str = None) -> str | None:
    """メイン関数。成功した場合は画像ファイルパスを、失敗した場合はNoneを返す。"""
    print("--- シーン画像生成ツール ---")
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

    if input_story_content and input_story_name:
        story_content, story_name = input_story_content, input_story_name
        print(f"物語テーマ (引数から): {story_name}")
    else:
        # この部分はオーケストレーターからは呼ばれないが、スタンドアロン実行のために残す
        print("エラー: 物語のコンテンツと名前が指定されていません。", file=sys.stderr)
        return None

    summary_text = clean_text_for_image(story_content, max_length=150)
    if not summary_text.strip():
        print("エラー: 画像にするテキスト内容がありません。", file=sys.stderr)
        return None
    print(f"画像テキスト: {summary_text}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_story_name = re.sub(r'[^\w\-_\. ]', '_', story_name.replace('.md', ''))
    output_filename = f"scene_{safe_story_name}_{timestamp}.png"
    output_filepath = os.path.join(IMAGE_OUTPUT_DIR, output_filename)
    
    success = generate_image_from_text(summary_text, output_filepath)

    print("--- シーン画像生成完了 ---")
    
    if success:
        return output_filepath
    else:
        return None

if __name__ == "__main__":
    # スタンドアロン実行用のロジック
    if len(sys.argv) == 3:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                content = f.read()
            # mainを呼び出し、結果に基づいてexitコードを設定
            result_path = main(content, sys.argv[2])
            if result_path:
                print(f"生成成功: {result_path}")
                sys.exit(0)
            else:
                sys.exit(1)
        except Exception as e:
            print(f"エラー: コマンドライン引数からの物語読み込み中にエラー: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("使用法: python generate_scene_images.py <story_filepath> <story_name>", file=sys.stderr)
        # 引数なしのmain()は失敗するのでNoneが返る想定
        if main() is None:
             sys.exit(1)
