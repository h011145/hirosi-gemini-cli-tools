# daily_feature_proposer_evolution.py

import json
import os
import random
import asyncio
from datetime import datetime, timedelta

# aiohttp が必要なので、必ず仮想環境で pip install aiohttp を実行してください
import aiohttp

# ==============================================================================
# グローバル変数と設定（必要に応じて調整）
# ==============================================================================
# Gemini API のエンドポイント
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
# API キーは環境変数から取得することを推奨
API_KEY = os.getenv("GEMINI_API_KEY", "") # 環境変数に GEMINI_API_KEY を設定してください

# ==============================================================================
# ヘルパー関数
# ==============================================================================

async def call_gemini_api(prompt, api_key):
    """
    Gemini API を呼び出してテキストを生成する非同期関数。
    """
    headers = {
        'Content-Type': 'application/json',
    }
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "featureName": {"type": "STRING"},
                        "description": {"type": "STRING"},
                        "priority": {"type": "STRING", "enum": ["Low", "Medium", "High"]},
                        "estimatedEffortDays": {"type": "NUMBER"}
                    },
                    "required": ["featureName", "description", "priority", "estimatedEffortDays"]
                }
            }
        }
    }

    # API キーを URL に追加
    api_url_with_key = f"{GEMINI_API_URL}?key={api_key}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url_with_key, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                        # JSON 文字列として返されるのでパース
                        json_string = result["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(json_string)
                    else:
                        print(f"Gemini API から予期しないレスポンス構造: {result}")
                        return None
                else:
                    error_text = await response.text()
                    print(f"Gemini API エラー: ステータス {response.status}, レスポンス: {error_text}")
                    return None
    except aiohttp.ClientError as e:
        print(f"HTTP リクエストエラー: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON デコードエラー: {e}, レスポンス: {json_string}")
        return None
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return None

def save_proposals(proposals, filename="feature_proposals.json"):
    """提案された機能をJSONファイルに保存する。"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(proposals, f, ensure_ascii=False, indent=4)
        print(f"提案された機能が '{filename}' に保存されました。")
    except IOError as e:
        print(f"ファイルの保存中にエラーが発生しました: {e}")

def load_proposals(filename="feature_proposals.json"):
    """保存された提案された機能をJSONファイルから読み込む。"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSONファイルの読み込み中にエラーが発生しました: {e}")
            return []
        except IOError as e:
            print(f"ファイルの読み込み中にエラーが発生しました: {e}")
            return []
    return []

# ==============================================================================
# メインの進化ステップ関数
# ==============================================================================

async def execute_evolution_step(self, context=None): # ここに 'self' を追加しました
    """
    daily_feature_proposer_evolution.py の主要な進化ステップを実行する関数。
    この関数がフレームワークによって呼び出されることを想定しています。
    """
    print("daily_feature_proposer_evolution.py: 進化ステップを開始します...")

    # ここに、既存の daily_feature_proposer_evolution.py の主要なロジックを配置します。
    # 例:
    # 1. 現在の状況や過去のデータを取得する (context を利用する可能性あり)
    # 2. Gemini API へのプロンプトを生成する
    # 3. Gemini API を呼び出して新しい機能の提案を得る
    # 4. 提案を保存する

    # 仮のプロンプト（必要に応じて詳細化してください）
    prompt = """
    あなたはユグドラシルの進化を促進するAIです。
    現在のユグドラシルの状況は以下の通りです。
    - ユーザーからのフィードバック: 「もっとゲームの種類を増やしてほしい」「UIがもっと直感的だと良い」
    - 開発状況: 現在、基本的なチャット機能とシンプルなツール連携が実装されています。
    - 目標: ユーザーエンゲージメントの向上と、より複雑なタスクへの対応。

    上記の状況に基づき、ユグドラシルに実装すべき新しい機能アイデアを3つ提案してください。
    各機能について、以下の情報をJSON形式の配列で提供してください。
    - featureName (文字列): 機能の簡潔な名前
    - description (文字列): 機能の詳細な説明
    - priority (文字列): 優先度 ("Low", "Medium", "High" のいずれか)
    - estimatedEffortDays (数値): 実装にかかる推定日数（整数）
    """

    print("Gemini API に機能提案をリクエスト中...")
    proposed_features = await call_gemini_api(prompt, API_KEY)

    if proposed_features:
        print("以下の機能が提案されました:")
        for feature in proposed_features:
            print(f"- {feature['featureName']} (優先度: {feature['priority']}, 予測工数: {feature['estimatedEffortDays']}日)")
        
        # 提案をファイルに保存
        save_proposals(proposed_features)
    else:
        print("機能の提案を取得できませんでした。")

    print("daily_feature_proposer_evolution.py: 進化ステップが完了しました。")

# ==============================================================================
# スクリプトが直接実行された場合の処理（オプション）
# ==============================================================================
if __name__ == "__main__":
    # このスクリプトが直接実行された場合、execute_evolution_step を呼び出す
    # 通常はフレームワークがこれを呼び出すため、このブロックはデバッグ用です。
    print("スクリプトが直接実行されました。")
    if not API_KEY:
        print("警告: GEMINI_API_KEY 環境変数が設定されていません。API呼び出しが失敗する可能性があります。")
        print("例: export GEMINI_API_KEY='YOUR_API_KEY_HERE'")
    
    # execute_evolution_step は 'self' を期待するため、ダミーのオブジェクトを渡す必要があります。
    # ここでは単純な object() インスタンスを渡しますが、
    # 実際のフレームワークがどのようなオブジェクトを渡すかによって調整が必要かもしれません。
    class DummySelf:
        pass
    
    asyncio.run(execute_evolution_step(DummySelf()))

