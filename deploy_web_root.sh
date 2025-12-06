#!/bin/bash
# DESCRIPTION: /var/www/html/public の内容をGitHub Pagesにデプロイ（公開）します。

# --- Configuration ---
# 設定ファイルから読み込む
CONFIG_FILE="$(dirname "$0")/deploy_config.json"

# jqがインストールされているか確認
if ! command -v jq &> /dev/null
then
    echo "エラー: jq がインストールされていません。JSONを処理できません。" >&2
    echo "sudo apt install jq" >&2
    exit 1
fi

# 設定ファイルを読み込む
SITE_TITLE=$(jq -r '.site_title' "$CONFIG_FILE")
NOTE_LINK_URL=$(jq -r '.note_link.url' "$CONFIG_FILE")
NOTE_LINK_TEXT=$(jq -r '.note_link.text' "$CONFIG_FILE")
HTML_SITE_ROOT=$(jq -r '.html_site_root' "$CONFIG_FILE")

# デプロイ元のディレクトリは固定
PUBLIC_DIR="/var/www/html/public"
GITHUB_REPO_URL="https://github.com/h011145/hirosi-web-public.git" 

# --- Helper Function for Sitemap Generation ---
generate_sitemap() {
    echo "sitemap.xml を生成します..."
    
    # Sitemapのヘッダー部分
    echo '<?xml version="1.0" encoding="UTF-8"?>' > sitemap.xml
    echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' >> sitemap.xml

    # index.html へのエントリを追加
    # Note: /var/www/html/public の場合は index.html が常にトップにあると仮定
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

    for html_file_path in ./*.html;
    do
        if [[ "$html_file_path" != "./index.html" && "$html_file_path" != "./sitemap.xml" ]]; then # sitemap.xmlも除外
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

echo "--- Webルートデプロイ開始 ---"
echo "デプロイ元ディレクトリ: $PUBLIC_DIR"
echo "デプロイ先リポジトリ: $GITHUB_REPO_URL"

cd "$PUBLIC_DIR" || exit 1

# --- Step 0: Gitリポジトリの状態を初期化 ---
# public/ にはGitリポジトリが一つだけ存在し、originが適切に設定されていることを保証する
echo "Gitリポジトリを確実に初期化・設定します..."
if [ -d ".git" ]; then
    echo "  既存の.gitディレクトリを削除します..."
    rm -rf .git
fi
echo "  新規Gitリポジトリを初期化します。"
git init
git branch -M main # 初期化後に必ずmainブランチを作成
echo "  リモート'origin'を設定します。"
git remote add origin "$GITHUB_REPO_URL"

# リモートの最新状態を取得し、ローカルブランチをリモートに追従させる (初回プッシュ時はエラーになるが無視する)
git fetch origin main >/dev/null 2>&1 || true
git reset --hard origin/main >/dev/null 2>&1 || true
echo "Gitリポジトリの準備が完了しました。"


# --- Step 1: index.html の自動生成 ---
echo "index.html を自動生成します。"
    
# 既存のHTMLファイルをスキャンし、タイトルとファイル名を収集
NOVEL_LINKS=""
NOVEL_COUNT=0
HTML_FILES=()

shopt -s globstar
shopt -s nullglob  

for html_file_path in ./*.html;
do
    if [[ "$html_file_path" != "./index.html" ]]; then # index.htmlは今回の処理で生成されるので除外
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
    INDEX_CONTENT="<p>まだ作品がありません。Markdown-to-HTML コンバーターでHTMLファイルを生成してください。</p>"
else
    INDEX_CONTENT="<h2>格納ファイル一覧 ($NOVEL_COUNT ファイル)</h2>\n$NOVEL_LINKS"
fi

# サイトタイトルは設定ファイルから読み込む
# NOTE: SITE_TITLE は既にCONFIG_FILEから読み込まれているはず

# noteサイトへのリンクHTML
NOTE_LINK_HTML="<p><a href=\"${NOTE_LINK_URL}\" target=\"_blank\">${NOTE_LINK_TEXT}</a></p>\n"

# HTMLテンプレートを一時ファイルとして作成
temp_template_file=$(mktemp)
cat > "$temp_template_file" <<'EOF_HTML_TEMPLATE'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s</title>
</head>
<body>
    <h1>%s</h1>
    %s
    %s
</body>
</html>
EOF_HTML_TEMPLATE

# index.htmlを生成
printf "$(cat "$temp_template_file")" "$SITE_TITLE" "$SITE_TITLE" "$NOTE_LINK_HTML" "$INDEX_CONTENT" > "index.html"
rm "$temp_template_file"
echo "index.html の生成が完了しました。"


# --- Step 1.5: sitemap.xml の生成 ---
generate_sitemap # sitemap.xmlを生成

# --- Step 2: Gitデプロイ ---
echo "変更をコミットしてプッシュします..."
git add .

# コミットメッセージを引数で受け取るか、デフォルト値を使う
COMMIT_MESSAGE="Web root content update on $(date)"
if [ -n "$1" ]; then # 引数があればコミットメッセージにする
    COMMIT_MESSAGE="$1"
fi

# 変更がある場合のみコミットとプッシュを行う
if ! git diff-index --quiet HEAD --; then
    echo "変更はありません。デプロイをスキップします。"
else
    git commit -m "$COMMIT_MESSAGE"
    git push -u origin main
    echo "デプロイが完了しました！"
fi

echo "----------------------------------------"
echo "${HTML_SITE_ROOT} に数分後に反映されます。"
echo "--- 処理完了 ---"