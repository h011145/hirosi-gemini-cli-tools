#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: 音声ファイルと画像ファイルから動画を組み立てます。

import os
import sys
import subprocess
from datetime import datetime

# --- 定数 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "scripts", "generated_videos")

# --- ヘルパー関数 ---
def get_audio_duration(audio_filepath: str) -> float:
    """ffprobeを使って音声ファイルの長さを秒単位で取得する"""
    command = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', audio_filepath
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        if isinstance(e, FileNotFoundError):
            print("エラー: 'ffprobe' コマンドが見つかりません。FFmpegがインストールされているか確認してください。", file=sys.stderr)
        else:
            print(f"エラー: 音声長の取得中にffprobeの実行に失敗しました。\n{e.stderr}", file=sys.stderr)
        return 0.0

def assemble_video(audio_filepath: str, image_filepath: str, output_filepath: str) -> bool:
    """音声と画像から動画を組み立てる。成功すればTrue、失敗すればFalseを返す。"""
    print(f"動画を組み立て中: {output_filepath}")

    if not all(os.path.exists(p) for p in [audio_filepath, image_filepath]):
        print(f"エラー: 入力ファイルが見つかりません。音声: {audio_filepath}, 画像: {image_filepath}", file=sys.stderr)
        return False

    duration = get_audio_duration(audio_filepath)
    if duration <= 0:
        print("エラー: 有効な音声長を取得できませんでした。動画生成を中止します。", file=sys.stderr)
        return False

    command = [
        'ffmpeg', '-loop', '1', '-i', image_filepath, '-i', audio_filepath,
        '-c:v', 'libx264', '-t', str(duration), '-pix_fmt', 'yuv420p',
        '-vf', 'scale=1280:720', '-y', output_filepath
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print("動画ファイルの生成が完了しました。")
        if not os.path.exists(output_filepath):
             print(f"エラー: 動画生成は成功しましたが、ファイルが見つかりません: {output_filepath}", file=sys.stderr)
             return False
        return True
    except FileNotFoundError:
        print("エラー: 'ffmpeg' コマンドが見つかりません。FFmpegがインストールされているか確認してください。", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print("エラー: ffmpegの実行に失敗しました。", file=sys.stderr)
        print(f"コマンド: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"リターンコード: {e.returncode}", file=sys.stderr)
        print(f"エラー出力:\n{e.stderr}", file=sys.stderr)
        return False

# --- メイン処理 ---
def main(audio_filepath: str = None, image_filepath: str = None) -> str | None:
    """メイン関数。成功した場合は動画ファイルパスを、失敗した場合はNoneを返す。"""
    print("--- 動画組み立てツール ---")
    os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)

    if not audio_filepath or not image_filepath:
        print("エラー: 音声ファイルと画像ファイルのパスが引数として指定されていません。", file=sys.stderr)
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"assembled_video_{timestamp}.mp4"
    output_filepath = os.path.join(VIDEO_OUTPUT_DIR, output_filename)
    
    success = assemble_video(audio_filepath, image_filepath, output_filepath)

    print("--- 全処理完了 ---")

    if success:
        print(f"生成された動画ファイル: {output_filepath}")
        return output_filepath
    else:
        return None

if __name__ == "__main__":
    if len(sys.argv) == 3:
        result_path = main(sys.argv[1], sys.argv[2])
        if result_path:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("使用法: python assemble_video.py <audio_file_path> <image_file_path>", file=sys.stderr)
        sys.exit(1)
