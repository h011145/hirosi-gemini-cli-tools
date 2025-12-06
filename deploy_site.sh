#!/bin/bash
# DESCRIPTION: 生成されたHTMLサイトをGitHub Pagesにデプロイ（公開）します。

# --- Configuration ---
PUBLIC_DIR="/home/hirosi/neo-world-saga-site/public"
GITHUB_REPO_URL="https://github.com/h011145/h011145.github.io.git" 
HTML_SITE_ROOT="https://h011145.github.io" # 公開サイトのルートURL

# --- Helper Function for Sitemap Generation ---
generate_sitemap() {
    echo "sitemap.xml を生成します..." 
    
    # Sitemapのヘッダー部分
    echo '<?xml version="1.0" encoding="UTF-8"?>' > sitemap.xml
    echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' >> sitemap.xml

    # index.html へのエントリを追加
    echo "  <url>" >> sitemap.xml
    echo "    <loc>${HTML_SITE_ROOT}/</loc>" >> sitemap.xml
    echo "    <lastmod>$(date -u +"%Y-%m-%dT%H:%M:%SZ")</lastmod>" >> sitemap.xml
    echo "    <changefreq>daily</changefreq>" >> sitemap.xml
    echo "    <priority>1.0</priority>" >> sitemap.xml
    echo "  </url>" >> sitemap.xml

    # その他のHTMLファイルへのエントリを追加
    # globstar を使用してカレントディレクトリの直下のHTMLファイルを探す
    shopt -s globstar # Enable recursive globbing for ** pattern
    shopt -s nullglob # Prevent glob from returning the pattern itself if no matches

    for html_file_path in ./*.html; do
        if [[ "$html_file_path" != "./index.html" ]]; then
            filename=$(basename "$html_file_path")
            echo "  <url>" >> sitemap.xml
            echo "    <loc>${HTML_SITE_ROOT}/$filename</loc>" >> sitemap.xml
            echo "    <lastmod>$(date -u +"%Y-%m-%dT%H:%M:%SZ")</lastmod>" >> sitemap.xml
            echo "    <changefreq>monthly</changefreq>" >> sitemap.xml
            echo "    <priority>0.8</priority>" >> sitemap.xml
            echo "  </url>" >> sitemap.xml
        fi
    done

    shopt -u globstar
    shopt -u nullglob

    # Sitemapのフッター部分
    echo '</urlset>' >> sitemap.xml
    echo "sitemap.xml の生成が完了しました。"
}


# --- Script Start ---
set -e # Exit on any error

echo "--- サイトデプロイ開始 ---"
cd "$PUBLIC_DIR" || exit 1

# --- Step 1: 作品一覧 (index.html) の自動生成 ---
echo "作品一覧 (index.html) を自動生成します..."

# 全てのHTMLファイルをスキャンし、タイトルとファイル名を収集
NOVEL_LINKS=""
NOVEL_COUNT=0
HTML_FILES=()

shopt -s globstar
shopt -s nullglob  

for html_file_path in ./*.html; do
    if [[ "$html_file_path" != "./index.html" ]]; then
        HTML_FILES+=("$html_file_path")
    fi
done

shopt -u globstar
shopt -u nullglob

IFS=$'\n' sorted_html_files=($(sort <<<"${HTML_FILES[*]}"))
unset IFS

for html_file_path in "${sorted_html_files[@]}"; do
    filename=$(basename "$html_file_path")
    title_from_filename=$(echo "$filename" | sed 's/\.html$//' | sed 's/_/ /g')
    relative_url="/$filename"
    
    NOVEL_LINKS+="<p><a href=\"$relative_url\">$title_from_filename</a></p>\n"
    NOVEL_COUNT=$((NOVEL_COUNT+1))
done


if [ "$NOVEL_COUNT" -eq 0 ]; then
    INDEX_CONTENT="<p>まだ作品がありません。コンバーターでHTMLファイルを生成してください。</p>"
else
    INDEX_CONTENT="<h2>作品一覧 ($NOVEL_COUNT 作品)</h2>\n$NOVEL_LINKS"
fi

SITE_TITLE="ネオワールドサーガ 作品サイト"

# HTMLテンプレートを一時ファイルとして作成
temp_template_file=$(mktemp)
cat > "$temp_template_file" <<'EOF_HTML_TEMPLATE'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s</title>
    <style>
        body {
            font-family: 'Hiragino Mincho ProN', 'MS PMincho', 'MS Mincho', serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background-color: #fdfdfd;
            color: #333;
        }
        h1, h2, h3 {
            font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 2em;
        }
        h1 {
            text-align: center;
            font-size: 2em;
            border-bottom: none;
        }
        p {
            margin: 1em 0;
        }
        a {
            color: #005ab4;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>%s</h1>
    %s
</body>
</html>
EOF_HTML_TEMPLATE

# index.htmlを生成
printf "$(cat "$temp_template_file")" "$SITE_TITLE" "$SITE_TITLE" "$INDEX_CONTENT" > "index.html"

# 一時ファイルを削除
rm "$temp_template_file"

echo "作品一覧 (index.html) を生成しました。"

# --- Step 1.5: sitemap.xml の生成 ---
generate_sitemap # sitemap.xmlを生成

# --- Step 2: Gitデプロイ ---
echo "Gitリポジトリを準備しています..."
# Gitリポジトリでなければ初期化する
if [ ! -d ".git" ]; then
    git init
    git branch -M main
fi
# リモートリポジトリが設定されていなければ設定する
if ! git remote -v | grep -q "origin"; then
    git remote add origin "$GITHUB_REPO_URL"
fi

git add .

# コミットメッセージを引数で受け取るか、デフォルト値を使う
COMMIT_MESSAGE="Site update on $(date)"
if [ -n "$1" ]; then # 引数があればコミットメッセージにする
    COMMIT_MESSAGE="$1"
fi

# 変更がある場合のみコミットを試みる
if ! git diff-index --quiet HEAD --; then
    git commit -m "$COMMIT_MESSAGE"
    git push -u origin main
    echo "デプロイが完了しました！"
else
    echo "変更はありません。デプロイをスキップします。"
fi

echo "----------------------------------------"
echo "${HTML_SITE_ROOT} に数分後に反映されます。"
echo "--- 処理完了 ---"