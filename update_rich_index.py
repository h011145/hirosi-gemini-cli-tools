#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*- 
# DESCRIPTION:リッチなindex.htmlに、/var/www/html/public内の他のHTMLファイルへのリンクを追加します。

import os
import glob
from bs4 import BeautifulSoup
import re # for clean filename

PUBLIC_DIR = "/var/www/html/public"
INDEX_HTML_PATH = os.path.join(PUBLIC_DIR, "index.html")

def generate_other_content_card(html_files_to_link: list[str]) -> str:
    """
    その他のコンテンツのカードセクションのHTMLを生成する
    """
    if not html_files_to_link:
        return ""

    links_html = ""
    for file_path in sorted(html_files_to_link):
        filename = os.path.basename(file_path)
        # ファイル名をタイトルに変換 (例: "neo_world_saga.html" -> "neo world saga")
        title = filename.replace('.html', '').replace('_', ' ')
        # 日本語ファイル名の場合はそのまま使用
        if re.search(r'[ぁ-んァ-ヶ一-龠]', title):
            display_title = title
        else:
            # それ以外は、パスをURLエンコードしたものをリンクに、タイトルを整形したものに
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
        print(f"エラー: {INDEX_HTML_PATH} が見つかりません。")
        return

    # index.html以外のHTMLファイルを取得
    all_html_files = []
    for root, _, files in os.walk(PUBLIC_DIR):
        for name in files:
            if name.endswith(".html") and name != "index.html":
                all_html_files.append(os.path.join(root, name))
    
    # 相対パスに変換
    html_files_to_link = [os.path.relpath(f, PUBLIC_DIR) for f in all_html_files]

    # その他のコンテンツカードのHTMLを生成
    other_content_card = generate_other_content_card(html_files_to_link)

    if not other_content_card:
        print("追加するHTMLファイルが見つかりませんでした。")
        return

    # index.htmlを読み込みBeautifulSoupで解析
    with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # 既存のカードセクションのrowを見つける
    # <div class="row"> の最後のものを見つけ、その直後に追加
    target_row = soup.find_all('div', class_='row')[-1] # 最後のrowを見つける

    if target_row:
        # 新しいカードセクションを解析
        new_soup = BeautifulSoup(other_content_card, 'html.parser')
        # 新しいrowを追加
        new_row = soup.new_tag("div", class_="row")
        new_row.append(new_soup) # 新しいカードを追加
        target_row.insert_after(new_row)
        print("新しいコンテンツセクションを追加しました。")
    else:
        print("エラー: ターゲットとなるrowセクションが見つかりませんでした。コンテンツを追加できませんでした。")
        return

    # 修正されたindex.htmlを書き出す
    with open(INDEX_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(soup.prettify(formatter="html"))
    
    print(f"{INDEX_HTML_PATH} を更新しました。")

if __name__ == "__main__":
    main()
