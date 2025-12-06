# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Yggdrasil Prototype: sample_evolution.py
# Version: 1.0.0
# Description: ユーザー定義の進化モジュールのサンプル。
#              apps.jsonに新しいアプリを追加し、ログにメッセージを記録します。
# Category: ユーザー定義
# -----------------------------------------------------------------------------

import logging

def execute_evolution_step(app_configs: list, logger_instance: logging.Logger) -> list:
    """
    この関数はEvolution Overseerによって呼び出され、カスタム進化ロジックを実行します。
    
    Args:
        app_configs (list): 現在のアプリ設定のリスト。
        logger_instance (logging.Logger): Evolution Overseerのロガーインスタンス。
    
    Returns:
        list: 更新されたアプリ設定のリスト。
    """
    logger_instance.info("サンプル進化モジュールが実行されました！")
    print("サンプル進化モジュール: apps.jsonに新しいアプリを追加します。")

    new_app_name = "user_custom_app.py"
    
    # 既存のアプリリストに新しいアプリがなければ追加
    existing_app_filenames = {app.get('filename') for app in app_configs if app.get('filename')}

    if new_app_name not in existing_app_filenames:
        new_app = {
            "filename": new_app_name,
            "path": f"apps/{new_app_name}",
            "description": "ユーザーが追加したカスタムアプリのサンプル。",
            "category": "ユーザーカスタム",
            "enabled": True,
            "quality_score": 0.7,
            "version": "1.0.0"
        }
        app_configs.append(new_app)
        logger_instance.info(f"新しいアプリ '{new_app_name}' を apps.json に追加しました。")
        print(f"「{new_app_name}」がapps.jsonに追加されました。")
    else:
        logger_instance.info(f"アプリ '{new_app_name}' は既に存在します。スキップします。")
        print(f"「{new_app_name}」は既に存在します。")

    logger_instance.info("サンプル進化モジュールが完了しました。")
    return app_configs

# このモジュールが直接実行された場合のテスト用
if __name__ == "__main__":
    # テスト用のダミーロガーとアプリ設定
    test_logger = logging.getLogger('test_logger')
    if not test_logger.handlers:
        test_handler = logging.StreamHandler()
        test_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        test_logger.addHandler(test_handler)
    test_logger.setLevel(logging.INFO)

    dummy_app_configs = [
        {"filename": "existing_app.py", "path": "apps/existing_app.py", "description": "既存のアプリ", "category": "テスト", "enabled": True, "quality_score": 1.0, "version": "1.0.0"}
    ]
    
    print("--- サンプル進化モジュールのスタンドアロンテスト ---")
    updated_configs = execute_evolution_step(dummy_app_configs, test_logger)
    print("\n更新されたアプリ設定:")
    for app in updated_configs:
        print(f"- {app['filename']} (カテゴリ: {app['category']})")
    print("--- テスト完了 ---")
