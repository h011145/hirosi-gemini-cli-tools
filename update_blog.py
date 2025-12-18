#!/home/hirosi/my_gemini_project/venv/bin/python
# -*- coding: utf-8 -*-
# DESCRIPTION: /var/www/html/public/blog.htmlに新しい開発記録を追加します。

import os
import sys
import markdown
from bs4 import BeautifulSoup

BLOG_HTML_PATH = "/var/www/html/public/blog.html"
NEW_ENTRY_MARKDOWN = """
### 2025年12月7日の開発記録

本日、GitHub PagesへのWebサイトデプロイに関して、大規模なトラブルシューティングと改善を行いました。

**主な経緯と課題:**

*   **GitHub Pagesへの静的サイトデプロイの難航:**
    *   `h011145.github.io/hirosi-web-public` へのデプロイが初期段階で問題となり、最終的にGitHub Pagesの構成の複雑さを理解するため、`h011145.github.io/hirosi-web-test-02` という新しいテストリポジトリを立ち上げました。
    *   `.nojekyll` ファイルの重要性：プロジェクトページでは、MarkdownファイルがあるとGitHub PagesがJekyllビルドを試みるため、`static`なサイトであることを明示する`.nojekyll`ファイルが必要であることが再確認されました。
    *   `base href` の問題：プロジェクトサイトのURL構造 (`username.github.io/repo-name/`) に合わせるため、`index.html` 内の`<base href>`タグの正しい設定が不可欠でした。
    *   `gh-pages` ブランチの利用：`main` ブランチからの直接公開がうまくいかないプロジェクトサイトでは、`gh-pages` ブランチへのデプロイがより確実な方法であることが判明しました。
    *   `deploy_web_test_02.sh` の改善：これまでのデプロイ中に判明したGitの不具合（ローカルとリモートの同期問題、変更検知のロジック）を修正し、より堅牢なスクリプトとなりました。
    *   `index.html` の生成ロジック：ユーザーが直接管理したいという意図を尊重し、`deploy_web_test_02.sh` から `index.html` 自動生成ロジックを削除しました。
    *   `その他のコンテンツ`の表示：`update_rich_index.py` を使用して、`index.html` にサイト内の他のHTMLファイルへの動的なリンクリストを追加しました。
    *   `リンク表示名のカスタマイズ機能`：`link_display_names.json` を導入し、リンクの表示名をユーザーが自由に設定できるようにしました。

*   **最終的な問題解決：Markdownファイルの干渉**
    *   `/var/www/html/public` ディレクトリ内に`.md`ファイルが多数存在することが、GitHub Pagesがサイトを正しく提供できない原因の一つであることが判明しました。GitHub Pagesは`.md`ファイルをHTMLに変換せず、そのままプッシュすると不都合が生じるため、これらを削除しました。

**結果:**

これらの改善と修正により、`h011145.github.io/hirosi-web-test-02` は、 `/var/www/html/public` ディレクトリ内のコンテンツをGitHub Pagesに正しくデプロイし、表示できるようになりました。
"""

def main():
    if not os.path.exists(BLOG_HTML_PATH):
        print(f"エラー: {BLOG_HTML_PATH} が見つかりません。blog.html が存在することを確認してください。", file=sys.stderr)
        return

    # 既存のblog.htmlを読み込み
    with open(BLOG_HTML_PATH, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # MarkdownをHTMLに変換
    new_entry_html = markdown.markdown(NEW_ENTRY_MARKDOWN, extensions=['fenced_code', 'tables'])

    # 新しいHTMLをBeautifulSoupオブジェクトとして解析
    new_soup_entry = BeautifulSoup(new_entry_html, 'html.parser')

    # 既存のbodyタグのフッターの前に挿入 (既存の<div class="container mt-5">の直後など)
    # 理想的には特定のコンテンツ領域に挿入したいが、ここではbodyの最後に近い位置を探す
    
    # <footer>タグを探してその直前に追加
    footer = soup.find('footer')
    if footer:
        footer.insert_before(new_soup_entry)
        print("フッターの前に新しいブログエントリを追加しました。")
    else:
        # footerがない場合はbodyの最後に近い場所を探す
        body = soup.find('body')
        if body:
            # 最後のスクリプトタグの前に挿入 (もしあれば)
            last_script = body.find_all('script')[-1] if body.find_all('script') else None
            if last_script:
                last_script.insert_before(new_soup_entry)
                print("最後のスクリプトタグの前に新しいブログエントリを追加しました。")
            else:
                body.append(new_soup_entry)
                print("bodyの最後尾に新しいブログエントリを追加しました。")
        else:
            print("エラー: bodyタグが見つかりませんでした。新しいブログエントリを追加できませんでした。", file=sys.stderr)
            return

    # 修正されたblog.htmlを書き出す
    with open(BLOG_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(soup.prettify(formatter="html"))
    
    print(f"{BLOG_HTML_PATH} を更新しました。")

if __name__ == "__main__":
    main()
