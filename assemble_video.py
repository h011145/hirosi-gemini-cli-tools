#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: テキストからImageMagickとffmpegを直接使用して、テキストが順番に表示される動画を生成します。

import os
import sys
import re
import subprocess
import tempfile
import shutil
from datetime import datetime

# --- 定数 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "scripts", "generated_videos")
# フォントはImageMagickが見つけられる名前を指定。-fontで指定。
FONT = "Noto-Sans-JP" # 'TakaoPGothic' なども候補
WIDTH, HEIGHT = 1280, 720
FPS = 24

def generate_image_for_scene(scene_text: str, output_path: str) -> bool:
    """ImageMagickを使って、1つのシーンのテキスト画像を生成する"""
    command = [
        'convert',
        '-background', 'black',
        '-fill', 'white',
        '-font', FONT,
        '-size', f'{WIDTH-100}x{HEIGHT-100}',
        '-gravity', 'center',
        f'caption:{scene_text}',
        output_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        return True
    except Exception as e:
        print(f"エラー: ImageMagickでの画像生成に失敗しました: {e}", file=sys.stderr)
        if hasattr(e, 'stderr'):
            print(e.stderr, file=sys.stderr)
        return False

# --- メイン処理 ---
def main(story_content: str, story_name: str, audio_filepath: str = None) -> str | None:
    """ImageMagickとffmpegを使って動画を生成する"""
    print("--- ImageMagick/ffmpeg 動画組み立てツール ---")
    os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)

    if not story_content or not story_name:
        print("エラー: 物語のコンテンツと名前が必要です。", file=sys.stderr)
        return None

    # 一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp(prefix="video_gen_")
    print(f"一時ディレクトリを作成: {temp_dir}")

    try:
        # 1. テキストをシーン（段落）に分割
        scenes_text = [p.strip() for p in story_content.split('\n') if p.strip()]
        if not scenes_text:
            print("エラー: 動画にするテキスト内容がありません。", file=sys.stderr)
            return None

        # 2. ffmpegのconcat demuxer用の入力ファイルリストを作成
        ffmpeg_input_file = os.path.join(temp_dir, "ffmpeg_input.txt")
        image_files = []
        with open(ffmpeg_input_file, 'w', encoding='utf-8') as f:
            for i, scene_text in enumerate(scenes_text):
                image_path = os.path.join(temp_dir, f"scene_{i:03d}.png")
                
                if not generate_image_for_scene(scene_text, image_path):
                    print(f"シーン {i+1} の画像生成に失敗したため、中止します。")
                    return None
                
                duration = max(3.0, len(scene_text) / 15.0)
                f.write(f"file '{image_path}'\n")
                f.write(f"duration {duration}\n")
                image_files.append(image_path)
        
        # 最後の画像のエントリを追記（concat demuxerの仕様）
        if image_files:
            with open(ffmpeg_input_file, 'a', encoding='utf-8') as f:
                f.write(f"file '{image_files[-1]}')\n")

        # 3. ffmpegで静止画から無音動画を生成
        silent_video_path = os.path.join(temp_dir, "silent_video.mp4")
        ffmpeg_cmd1 = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', ffmpeg_input_file,
            '-vf', f'fps={FPS},format=yuv420p',
            '-y',
            silent_video_path
        ]
        print("ffmpegで無音動画を生成中...")
        subprocess.run(ffmpeg_cmd1, check=True, capture_output=True, text=True, encoding='utf-8')

        # 4. ffmpegで音声と無音動画を合成
        # ファイル名を安全にするための正規表現を修正
        safe_story_name = re.sub(r'[^\w._ -]', '_', story_name.replace('.md', ''))
        final_output_filename = f"assembled_video_{safe_story_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        final_output_path = os.path.join(VIDEO_OUTPUT_DIR, final_output_filename)
        
        ffmpeg_cmd2 = [
            'ffmpeg',
            '-i', silent_video_path,
        ]
        if audio_filepath and os.path.exists(audio_filepath):
            print(f"音声ファイル {audio_filepath} を合成中...")
            ffmpeg_cmd2.extend(['-i', audio_filepath])
            # -shortest オプションで、短い方のストリームの長さに合わせる
            ffmpeg_cmd2.extend(['-c:v', 'copy', '-c:a', 'aac', '-shortest'])
        else:
            print("音声なしで動画を最終処理中...")
            ffmpeg_cmd2.extend(['-c', 'copy'])
        
        ffmpeg_cmd2.extend(['-y', final_output_path])

        subprocess.run(ffmpeg_cmd2, check=True, capture_output=True, text=True, encoding='utf-8')

        print(f"動画ファイルの生成が完了しました: {final_output_path}")
        return final_output_path

    except Exception as e:
        print(f"エラー: 動画生成のパイプライン中にエラーが発生しました: {e}", file=sys.stderr)
        if hasattr(e, 'stderr'):
            print("--- STDERR ---", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        return None
    finally:
        # 一時ディレクトリをクリーンアップ
        print(f"一時ディレクトリを削除: {temp_dir}")
        shutil.rmtree(temp_dir)
        print("--- 全処理完了 ---")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            story_file = sys.argv[1]
            story_name = os.path.basename(story_file)
            audio_file = sys.argv[2] if len(sys.argv) > 2 else None
            with open(story_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if main(content, story_name, audio_file):
                sys.exit(0)
            else:
                sys.exit(1)
        except Exception as e:
            print(f"エラー: 実行中にエラーが発生しました: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("使用法: python assemble_video.py <story_filepath> [audio_filepath]", file=sys.stderr)
        sys.exit(1)