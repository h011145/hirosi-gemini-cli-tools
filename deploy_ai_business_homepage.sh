#!/bin/bash
# DESCRIPTION: /var/www/html/public から ai_business_homepage.html と動画ファイルをAIビジネスホームページ実験用リポジトリにデプロイします。

# --- Configuration ---
CONFIG_FILE="$(dirname "$0")/deploy_config.json"

# jqがインストールされているか確認
if ! command -v jq &> /dev/null
then
    echo "エラー: jq がインストールされていません。JSONを処理できません。" >&2
    echo "sudo apt install jq" >&2
    exit 1
fi

SITE_TITLE=$(jq -r '.site_title' "$CONFIG_FILE")
PUBLIC_DIR="/var/www/html/public"
GITHUB_REPO_URL="https://github.com/h011145/ai-business-homepage-experiment.git"
HTML_SITE_ROOT="https://h011145.github.io/ai-business-homepage-experiment"
MAIN_PAGE="ai_business_homepage.html"
VIDEO_FILE_ARG="$1"
VIDEO_FILENAME=""

# --- Video File Handling ---
if [ -z "$VIDEO_FILE_ARG" ]; then
    echo "警告: デプロイする動画ファイルが指定されていません。" >&2
    # 動画なしでもデプロイは継続
else
    if [ ! -f "$VIDEO_FILE_ARG" ]; then
        echo "エラー: 指定された動画ファイルが見つかりません: $VIDEO_FILE_ARG" >&2
        exit 1
    fi
    VIDEO_FILENAME=$(basename "$VIDEO_FILE_ARG")
    echo "動画ファイル $VIDEO_FILENAME をデプロイ対象に追加します。"
    cp "$VIDEO_FILE_ARG" "$PUBLIC_DIR/$VIDEO_FILENAME"
    echo "動画ファイルを $PUBLIC_DIR にコピーしました。"
fi


# --- Helper Function for Sitemap Generation ---
generate_sitemap() {
    echo "sitemap.xml を生成します..."
    
    echo '<?xml version="1.0" encoding="UTF-8"?>' > sitemap.xml
    echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' >> sitemap.xml

    # メインページ
    echo "  <url><loc>${HTML_SITE_ROOT}/${MAIN_PAGE}</loc><lastmod>$(date -u +"%Y-%m-%dT%H:%M:%SZ")</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>" >> sitemap.xml

    # 動画ページ (動画があれば)
    if [ -n "$VIDEO_FILENAME" ]; then
        echo "  <url><loc>${HTML_SITE_ROOT}/${VIDEO_FILENAME}</loc><lastmod>$(date -u +"%Y-%m-%dT%H:%M:%SZ")</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>" >> sitemap.xml
    fi

    echo '</urlset>' >> sitemap.xml
    echo "sitemap.xml の生成が完了しました。"
}


# --- Script Start ---
set -e
echo "--- AIビジネスホームページデプロイ開始 ---"
cd "$PUBLIC_DIR" || exit 1

# --- Git Setup ---
if [ ! -d ".git" ]; then
    git init
    git branch -M main
    git remote add origin "$GITHUB_REPO_URL"
else
    if ! git remote -v | grep -q "origin"; then
        git remote add origin "$GITHUB_REPO_URL"
    fi
fi
touch .nojekyll

# --- File Cleanup ---
echo "不要なファイルをクリーンアップします..."
# find を使って、保持するファイル以外を削除する
# findコマンドは引数の扱いが複雑なので、より安全なループに切り替える
for file in * .*; do
    # ディレクトリや特殊なエントリはスキップ
    if [ ! -f "$file" ]; then
        continue
    fi
    # 保持するファイルかチェック
    case "$file" in
        "$MAIN_PAGE"|"index.html"|"sitemap.xml"|".nojekyll"|"$VIDEO_FILENAME")
            # 保持
            ;;
        *)
            # 削除
            echo "  - Deleting: $file"
            rm -f "$file"
            ;;
    esac
done


# サブディレクトリは.git以外すべて削除
find . -maxdepth 1 -type d ! -name ".git" ! -name "." -exec rm -rf {} +


# --- index.html Generation ---
echo "index.html を生成します (ai_business_homepage.htmlへリダイレクト)。"
cat > index.html <<EOF
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta http-equiv="refresh" content="0;url=./${MAIN_PAGE}"><title>Redirecting</title></head><body><p><a href="./${MAIN_PAGE}">Redirecting...</a></p></body></html>
EOF

# --- Sitemap Generation ---
generate_sitemap

# --- Git Deployment ---
echo "変更をコミットしてプッシュします..."
git add .
if git diff --cached --quiet; then
    echo "変更はありません。デプロイをスキップします。"
else
    COMMIT_MESSAGE="Site update on $(date)"
    git commit -m "$COMMIT_MESSAGE"
    git push -u origin main --force
    echo "デプロイが完了しました！"
fi

echo "----------------------------------------"
echo "${HTML_SITE_ROOT} に数分後に反映されます。"
# --- 処理完了 ---