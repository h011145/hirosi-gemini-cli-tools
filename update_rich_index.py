#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: リッチなindex.htmlに、/var/www/html/public内の他のHTMLファイルへのリンクを追加します。

import os
import glob
from bs4 import BeautifulSoup
import re # for clean filename
import json # for config file
import sys # 修正: sysモジュールをインポート

PUBLIC_DIR = "/var/www/html/public"
INDEX_HTML_PATH = os.path.join(PUBLIC_DIR, "index.html")
LINK_DISPLAY_NAMES_CONFIG = os.path.join(os.path.dirname(__file__), "link_display_names.json")

def load_display_names_config() -> dict:
    """リンク表示名設定ファイルを読み込む"""
    if not os.path.exists(LINK_DISPLAY_NAMES_CONFIG):
        return {}
    try:
        with open(LINK_DISPLAY_NAMES_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"エラー: {LINK_DISPLAY_NAMES_CONFIG} の読み込みに失敗しました。JSON形式が不正です: {e}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"エラー: {LINK_DISPLAY_NAMES_CONFIG} の読み込みに失敗しました: {e}", file=sys.stderr)
        return {}

def generate_other_content_card(html_files_to_link: list[str], display_names_map: dict) -> str:
    """
    その他のコンテンツのカードセクションのHTMLを生成する
    """
    if not html_files_to_link:
        return ""

    links_html = ""
    for file_path in sorted(html_files_to_link):
        filename = os.path.basename(file_path)
        
        # 設定ファイルに表示名があればそれを使用
        if filename in display_names_map:
            display_title = display_names_map[filename]
        else:
            # なければファイル名から自動生成
            title = filename.replace('.html', '').replace('_', ' ')
            if re.search(r'[ぁ-んァ-ヶ一-龠]', title): # 日本語を含む場合
                display_title = title
            else:
                display_title = title # Simple conversion for now

        links_html += f'<p><a href="{filename}" class="card-link">{display_title}</a></p>\n'


    card_html = f"""
    <div class="col-md-6 mb-4">
        <div class="card h-100">
            <div class="card-body">
                <h2 class="card-title">その他のコンテンツ</h2>
                <p class="card-text">サイト内に存在する、`index.html`以外のファイルへのリンクです。</p>
                {links_html}
            </div>
        </div>
    </div>
    """
    return card_html


def main():
    if not os.path.exists(INDEX_HTML_PATH):
        print(f"エラー: {INDEX_HTML_PATH} が見つかりません。", file=sys.stderr) # sys.stderr を明示的に指定
        return

    # リンク表示名設定を読み込む
    display_names_map = load_display_names_config()

    # index.html以外のHTMLファイルを取得
    all_html_files = []
    # os.listdirを使用
    for file in os.listdir(PUBLIC_DIR):
        if file.endswith(".html") and file != "index.html":
            all_html_files.append(file)
    
    # その他のコンテンツカードのHTMLを生成
    other_content_card = generate_other_content_card(all_html_files, display_names_map)

    if not other_content_card:
        print("追加するHTMLファイルが見つからなかったか、エラーが発生しました。", file=sys.stderr)
        return

    # index.htmlを読み込みBeautifulSoupで解析
    with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # 既存のカードセクションのrowを見つける
    # <div class="row"> の最後のものを見つけ、その直後に追加
    # ただし、すでに"その他のコンテンツ"カードが存在する場合は、それを更新する
    existing_other_content_card_title = soup.find('h2', class_='card-title', string='その他のコンテンツ')
    if existing_other_content_card_title:
        # 既存のカードを新しい内容で置き換える
        existing_other_content_card_parent = existing_other_content_card_title.find_parent('div', class_='col-md-6')
        if existing_other_content_card_parent:
            new_soup = BeautifulSoup(other_content_card, 'html.parser')
            existing_other_content_card_parent.replace_with(new_soup.find('div', class_='col-md-6'))
            print("既存の「その他のコンテンツ」セクションを更新しました。")
        else:
            print("エラー: 既存の「その他のコンテンツ」カードの親要素が見つかりませんでした。", file=sys.stderr)
            return
    else:
        # 新しいカードセクションを解析して挿入
        target_row = soup.find_all('div', class_='row')
        if target_row:
            # 最後のrow要素を取得
            main_container = soup.find('div', class_='container mt-5')
            if main_container:
                last_row = main_container.find_all('div', class_='row')[-1]
                new_soup = BeautifulSoup(other_content_card, 'html.parser')
                # BeautifulSoupのtagオブジェクトをそのままinsert_afterに渡す
                # new_row = soup.new_tag("div", class_="row") # これだとnew_soupのタグがそのまま挿入されないのでやめる
                # new_row.append(new_soup) 
                last_row.insert_after(new_soup.find('div', class_='col-md-6').parent) # generated card is within a col-md-6, parent is a row

                print("新しいコンテンツセクションを追加しました。")
            else:
                print("エラー: メインコンテナが見つかりませんでした。コンテンツを追加できませんでした。", file=sys.stderr)
                return
        else:
            print("エラー: ターゲットとなるrowセクションが見つかりませんでした。コンテンツを追加できませんでした。", file=sys.stderr)
            return

    # 修正されたindex.htmlを書き出す
    with open(INDEX_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(soup.prettify(formatter="html"))
    
    print(f"{INDEX_HTML_PATH} を更新しました。")

if __name__ == "__main__":
    main()
