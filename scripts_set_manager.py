#!/usr/bin/env python3
# DESCRIPTION: Yggdrasil Prototype アプリセットマネージャー
# CATEGORY: ファイル管理

import os
import sys
import shutil
import json

# プロジェクトルートを設定し、ユーティリティモジュールをインポートできるようにする
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_name = "my_gemini_project" 

PROJECT_ROOT = _current_dir
while not os.path.basename(PROJECT_ROOT) == _project_name and PROJECT_ROOT != '/':
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)

if os.path.basename(PROJECT_ROOT) != _project_name:
    print(f"Error: Could not find project root directory '{_project_name}'. Current path: {os.getcwd()}", file=sys.stderr)
    sys.exit(1)

# utilsディレクトリをPythonの検索パスに追加
utils_path = os.path.join(PROJECT_ROOT, 'utils')
if os.path.isdir(utils_path) and utils_path not in sys.path:
    sys.path.append(utils_path)

# 必要なユーティリティをインポート
try:
    from display_utils import print_header, get_user_input, press_enter_to_continue, print_result, print_error, select_from_list
    from file_utils import get_script_files_in_dir, create_safe_filename
except ImportError as e:
    print(f"Error: Essential utility modules not found. Check 'utils' directory. {e}", file=sys.stderr)
    sys.exit(1)

# --- 定数 ---
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
ARCHIVE_DIR = os.path.join(PROJECT_ROOT, 'archive_scripts')
CONFIGS_DIR = os.path.join(PROJECT_ROOT, 'configs')
DEFAULT_CONFIG_FILE_EXT = ".json" # JSON形式で設定を保存

# ディレクトリが存在しない場合は作成
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(CONFIGS_DIR, exist_ok=True)

# --- ヘルパー関数 ---

def _get_all_scripts_by_status():
    """
    scripts/ と archive_scripts/ 内の全てのスクリプトの情報を返す。
    return: (active_scripts_info, archived_scripts_info)
            各infoは {"filename": "ファイル名.py", "path": "/フル/パス/ファイル名.py"} の辞書リスト
    """
    active_scripts_paths = get_script_files_in_dir(SCRIPTS_DIR)
    archived_scripts_paths = get_script_files_in_dir(ARCHIVE_DIR)

    active_scripts_info = [{"filename": os.path.basename(p), "path": p} for p in active_scripts_paths]
    archived_scripts_info = [{"filename": os.path.basename(p), "path": p} for p in archived_scripts_paths]

    # menu.sh は常にアクティブリストから除外
    active_scripts_info = [s for s in active_scripts_info if s["filename"] != "menu.sh"]

    # 重複を避ける（同じファイルが両方のリストに存在しないことを確認）
    # scripts/ に存在するファイルは、archived_scripts/ から除外する
    active_filenames = {s["filename"] for s in active_scripts_info}
    archived_scripts_info = [s for s in archived_scripts_info if s["filename"] not in active_filenames]

    return active_scripts_info, archived_scripts_info

def _move_script(src_path: str, dest_dir: str) -> bool:
    """
    スクリプトを移動する。
    """
    try:
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        shutil.move(src_path, dest_path)
        return True
    except FileNotFoundError:
        print_error(f"移動元ファイルが見つかりません: {src_path}")
        return False
    except shutil.Error as e:
        print_error(f"ファイルの移動に失敗しました ({os.path.basename(src_path)} から {os.path.basename(dest_dir)}): {e}")
        return False
    except Exception as e:
        print_error(f"予期せぬエラーで移動に失敗しました ({os.path.basename(src_path)}): {e}")
        return False

def _save_app_set(set_name: str, active_scripts_info: list) -> bool:
    """
    現在のscripts/ディレクトリにあるアプリのセットをJSONファイルとして保存する。
    """
    if not set_name.strip():
        print_error("セット名が入力されていません。")
        return False

    safe_set_name = create_safe_filename(set_name)
    config_filepath = os.path.join(CONFIGS_DIR, f"{safe_set_name}{DEFAULT_CONFIG_FILE_EXT}")

    # アクティブなスクリプトのファイル名のみを保存
    active_filenames = [s["filename"] for s in active_scripts_info]

    try:
        with open(config_filepath, 'w', encoding='utf-8') as f:
            json.dump(active_filenames, f, indent=4)
        print_result("アプリセット保存完了", f"現在のアプリセットを '{config_filepath}' に保存しました。")
        return True
    except Exception as e:
        print_error(f"アプリセットの保存に失敗しました: {e}")
        return False

def _load_app_set(set_name: str) -> list | None:
    """
    指定されたJSONファイルからアプリのセットを読み込む。
    """
    if not set_name.strip():
        print_error("セット名が入力されていません。")
        return None

    safe_set_name = create_safe_filename(set_name)
    config_filepath = os.path.join(CONFIGS_DIR, f"{safe_set_name}{DEFAULT_CONFIG_FILE_EXT}")

    if not os.path.exists(config_filepath):
        print_error(f"指定されたアプリセットファイルが見つかりません: {config_filepath}")
        return None

    try:
        with open(config_filepath, 'r', encoding='utf-8') as f:
            active_filenames = json.load(f)
        
        if not isinstance(active_filenames, list):
            print_error(f"アプリセットファイル '{config_filepath}' の形式が不正です。")
            return None
        
        return active_filenames
    except json.JSONDecodeError:
        print_error(f"アプリセットファイル '{config_filepath}' のJSON形式が不正です。")
        return None
    except Exception as e:
        print_error(f"アプリセットの読み込みに失敗しました: {e}")
        return None

def _get_available_sets():
    """
    保存されているアプリセットのファイル名（拡張子なし）リストを返す。
    """
    set_files = [f for f in os.listdir(CONFIGS_DIR) if f.endswith(DEFAULT_CONFIG_FILE_EXT)]
    return sorted([os.path.splitext(f)[0] for f in set_files]) # 拡張子なしのファイル名をソートして返す

def _edit_active_apps_flow():
    """
    アクティブなアプリを編集（アーカイブ/復元）するフロー。
    複数選択に対応。
    """
    while True:
        print_header("アクティブなアプリを編集 (複数選択可)")
        active_scripts, archived_scripts = _get_all_scripts_by_status()

        # オプションと内部マッピングを作成
        # {'A1': {'filename': 'app1.py', 'path': '...'}, 'R1': {'filename': 'app_arc.py', 'path': '...'}}
        display_options = []
        app_map = {} 
        current_idx = 1 # 1から始まるインデックス

        if active_scripts:
            display_options.append("--- 現在アクティブなアプリ (scripts/) ---")
            for app in active_scripts:
                key = f"A{current_idx}"
                display_options.append(f"{key}. [アクティブ] {app['filename']}")
                app_map[key] = app
                current_idx += 1
        
        if archived_scripts:
            if active_scripts: # 両方のリストがある場合にのみ区切りを追加
                display_options.append("") # 空行で区切り
            display_options.append("--- アーカイブ済みアプリ (archive_scripts/) ---")
            current_idx = 1 # アーカイブ済みは再度1から始まるインデックス
            for app in archived_scripts:
                key = f"R{current_idx}"
                display_options.append(f"{key}. [アーカイブ済み] {app['filename']}")
                app_map[key] = app
                current_idx += 1

        if not active_scripts and not archived_scripts:
            print_result("情報", "scripts/ディレクトリとarchive_scripts/ディレクトリにスクリプトが見つかりませんでした。")
            press_enter_to_continue()
            return # メインメニューに戻る

        print("\n--- 選択方法 ---")
        print("移動したいアプリの番号 (例: 'A1' または 'R2') を入力してください。")
        print("複数選択する場合は、カンマ区切りで入力してください (例: 'A1,R3,A5')。")
        print("b. 戻る (メインメニューへ)")
        print("q. 終了 (アプリを終了)")

        # select_from_list を呼び出す際、複数選択の指示はプロンプトに含める
        user_input_raw = get_user_input("選択してください: ")
        
        if user_input_raw.lower() == 'b':
            return # メインメニューに戻る
        elif user_input_raw.lower() == 'q':
            if get_user_input("本当にアプリを終了しますか？(y/n): ").lower() == 'y':
                sys.exit(0) # アプリケーション全体を終了
            else:
                continue # 編集を続行
        
        # ユーザー入力を解析して選択されたキーのリストを取得
        selected_keys_raw = [k.strip().upper() for k in user_input_raw.split(',') if k.strip()]
        
        selected_apps_to_process = []
        for key in selected_keys_raw:
            if key in app_map:
                selected_apps_to_process.append(app_map[key])
            else:
                print_error(f"無効な選択: '{key}'。スキップします。")

        if not selected_apps_to_process:
            print_error("有効なアプリが選択されませんでした。")
            press_enter_to_continue()
            continue

        # 選択されたアプリのリストを表示して確認
        print("\n--- 選択されたアプリ ---")
        for app_info in selected_apps_to_process:
            status = "[アクティブ]" if os.path.dirname(app_info['path']) == SCRIPTS_DIR else "[アーカイブ済み]"
            print(f"- {status} {app_info['filename']}")
        
        confirm = get_user_input("上記アプリを移動しますか？ (y/n): ").lower()
        if confirm != 'y':
            print("移動をキャンセルしました。")
            press_enter_to_continue()
            continue

        # 実際に移動処理を実行
        for app_info in selected_apps_to_process:
            source_dir = os.path.dirname(app_info['path'])
            
            if source_dir == SCRIPTS_DIR: # アクティブなアプリ -> アーカイブへ移動
                target_dir = ARCHIVE_DIR
                action_desc = "アーカイブ"
            elif source_dir == ARCHIVE_DIR: # アーカイブ済みアプリ -> アクティブへ移動 (復元)
                target_dir = SCRIPTS_DIR
                action_desc = "復元"
            else:
                print_error(f"不明なパスのアプリ: {app_info['filename']} - {app_info['path']}")
                continue

            if _move_script(app_info['path'], target_dir):
                print_result("移動完了", f"'{app_info['filename']}' を {action_desc} しました。")
            else:
                print_error(f"'{app_info['filename']}' の{action_desc}に失敗しました。")
        
        print_result("処理完了", "選択された全てのアプリの移動処理が完了しました。")
        press_enter_to_continue()

def _save_app_set_flow():
    """
    現在のアプリセットを保存するフロー。
    """
    print_header("アプリセットを保存")
    active_scripts, _ = _get_all_scripts_by_status()

    if not active_scripts:
        print_result("情報", "現在アクティブなアプリがありません。保存するセットがありません。")
        press_enter_to_continue()
        return

    set_name = get_user_input("保存するセットの名前を入力してください (例: my_dev_set): ")
    if _save_app_set(set_name, active_scripts):
        print("アプリセットが正常に保存されました。")
    else:
        print_error("アプリセットの保存に失敗しました。")
    press_enter_to_continue()

def _load_app_set_flow():
    """
    保存されているアプリセットを読み込むフロー。
    """
    while True:
        print_header("アプリセットを読み込む")
        available_sets = _get_available_sets()

        if not available_sets:
            print_result("情報", "保存されているアプリセットがありません。")
            press_enter_to_continue()
            return

        options = [s for s in available_sets] # 読み込むセット名だけを表示
        
        selected_set_index = select_from_list(options, "読み込みたいアプリセットを選択してください: ")

        if selected_set_index is None: # 'q' (終了) または 'b' (戻る) が選択された場合
            if get_user_input("本当に読み込みを終了してメニューに戻りますか？(y/n): ").lower() == 'y':
                return
            else:
                continue # もう一度選択肢を表示

        # select_from_list は1から始まるインデックスを返すため、-1する
        selected_set_name = options[selected_set_index - 1] 

        confirm = get_user_input(f"アプリセット '{selected_set_name}' を読み込みますか？現在の設定は上書きされます。(y/n): ").lower()
        if confirm != 'y':
            print("読み込みをキャンセルしました。")
            press_enter_to_continue()
            continue

        desired_active_filenames = _load_app_set(selected_set_name)

        if desired_active_filenames is None:
            press_enter_to_continue()
            continue # _load_app_set でエラーメッセージは表示済み

        print_result("アプリセット読み込み中", f"セット '{selected_set_name}' に基づいてアプリ構成を更新します。")
        
        # 現在の状況を取得
        current_active_scripts, current_archived_scripts = _get_all_scripts_by_status()

        # 1. 全ての現在アクティブなアプリを一時的にarchive_scriptsに移動（menu.sh以外）
        print("既存のアプリ構成をアーカイブしています...")
        for app in current_active_scripts:
            if app["filename"] != "menu.sh":
                if not _move_script(app["path"], ARCHIVE_DIR):
                    print_error(f"既存アクティブアプリ '{app['filename']}' のアーカイブに失敗しました。読み込みを中止します。")
                    press_enter_to_continue()
                    return # 失敗したら読み込みを中止

        # 2. 目的のアプリをarchive_scriptsからscriptsに移動
        print("新しいアプリ構成を適用しています...")
        # 最新のアーカイブ状態を再取得（前のステップで移動したものが含まれる）
        # ここで `_get_all_scripts_by_status()` はアーカイブディレクトリ内のファイルパスを
        # 更新された状態で取得するため、適切です。
        _, all_archived_scripts_after_initial_move = _get_all_scripts_by_status() 
        
        for desired_filename in desired_active_filenames:
            found_in_archive = False
            for app in all_archived_scripts_after_initial_move:
                if app["filename"] == desired_filename:
                    if _move_script(app["path"], SCRIPTS_DIR):
                        print(f"'{desired_filename}' をscripts/に復元しました。")
                    else:
                        print_error(f"'{desired_filename}' の復元に失敗しました。")
                    found_in_archive = True
                    break
            if not found_in_archive:
                print(f"警告: セット '{selected_set_name}' に含まれるファイル '{desired_filename}' がアーカイブに見つかりませんでした。")
                
        print_result("アプリセット読み込み完了", f"アプリ構成をセット '{selected_set_name}' に更新しました。")
        press_enter_to_continue()
        return # 読み込み成功したらメインメニューに戻る


def _show_managed_files_flow():
    """
    scripts/ と archive_scripts/ 内の管理対象ファイルを一覧表示するフロー。
    """
    print_header("管理対象ファイル一覧")
    active_scripts, archived_scripts = _get_all_scripts_by_status()

    if not active_scripts and not archived_scripts:
        print_result("情報", "管理対象のスクリプトファイルが見つかりませんでした。")
    else:
        if active_scripts:
            print_result("情報", "--- 現在アクティブなアプリ (scripts/) ---")
            for app in active_scripts:
                print_result("情報", f"- {app['filename']}")
        else:
            print_result("情報", "現在アクティブなアプリはありません。")

        if archived_scripts:
            print_result("情報", "\n--- アーカイブ済みアプリ (archive_scripts/) ---")
            for app in archived_scripts:
                print_result("情報", f"- {app['filename']}")
        else:
            print_result("情報", "アーカイブ済みアプリはありません。")
    
    press_enter_to_continue()


def main():
    print_header("Yggdrasil Prototype アプリセットマネージャー")

    while True:
        print("\n--- アプリセットマネージャーメニュー ---")
        print("1. アクティブなアプリを編集 (アーカイブ/復元)")
        print("2. アプリセットを保存")
        print("3. アプリセットを読み込む")
        print("4. 整理するファイルを表示")
        print("5. 終了")
        
        choice = get_user_input("選択してください (1-5): ")

        if choice == '1':
            _edit_active_apps_flow()
        elif choice == '2':
            _save_app_set_flow()
        elif choice == '3':
            _load_app_set_flow()
        elif choice == '4':
            _show_managed_files_flow()
        elif choice == '5':
            print("アプリセットマネージャーを終了します。")
            break
        else:
            print_error("無効な選択です。1から5の番号を入力してください。")
            press_enter_to_continue()

if __name__ == "__main__":
    main()