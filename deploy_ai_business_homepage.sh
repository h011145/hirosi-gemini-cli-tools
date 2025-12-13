#!/bin/bash
# DESCRIPTION: /var/www/html/public の内容をAIビジネスホームページ実験用リポジトリにデプロイします。

# --- Configuration ---
# 設定ファイルから読み込む (deploy_config.jsonは既存のものを利用)
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

# デプロイ元のディレクトリは固定
PUBLIC_DIR="/var/www/html/public"
# AIビジネスホームページ実験用リポジトリのURL
GITHUB_REPO_URL="https://github.com/h011145/ai-business-homepage-experiment.git" 
# 公開サイトのルートURL
HTML_SITE_ROOT="https://h011145.github.io/ai-business-homepage-experiment" 


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
    shopt -s globstar # Enable recursive globbing for ** pattern
    shopt -s nullglob # Prevent glob from returning the pattern itself if no matches

    for html_file_path in ./*.html;
    do
        if [[ "$html_file_path" != "./index.html" && "$html_file_path" != "./sitemap.xml" ]]; then
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

echo "--- AIビジネスホームページデプロイ開始 ---"
echo "デプロイ元ディレクトリ: $PUBLIC_DIR"
echo "デプロイ先リポジトリ: $GITHUB_REPO_URL"

cd "$PUBLIC_DIR" || exit 1

# --- Step 0: Gitリポジリを確実に初期化・設定します... ---
echo "Gitリポジリを確実に初期化・設定します..."
# .gitディレクトリが存在しない場合は初期化
if [ ! -d ".git" ]; then
    echo "  .gitディレクトリがありません。新規Gitリポジリを初期化します。"
    git init
    git branch -M main # username.github.io の場合、mainブランチにプッシュ
    echo "  リモート'origin'を設定します。"
    git remote add origin "$GITHUB_REPO_URL"
else
    # 既存のリポジリの場合、リモート'origin'が存在するか確認し、なければ設定
    if ! git remote -v | grep -q "origin"; then
        echo "  リモート'origin'が設定されていません。設定します。"
        git remote add origin "$GITHUB_REPO_URL"
    elif ! git remote -v | grep -q "$GITHUB_REPO_URL"; then
        echo "  リモート'origin'が現在のリポジリURLと一致しません。削除して再設定します。"
        git remote remove origin
        git remote add origin "$GITHUB_REPO_URL"
    fi
    # ローカルブランチがmainであることを確認
    if ! git rev-parse --abbrev-ref HEAD | grep -q "main"; then
        echo "  ローカルブランチを'main'に設定します。"
        git checkout -b main || git branch -M main
    fi
    # リモートから最新の状態をフェッチするが、ローカルファイルを上書きしない (ローカルの変更を優先するため)
    git fetch origin >/dev/null 2>&1 || true
fi
echo "Gitリポジトリの準備が完了しました。"

# --- Step 0.5: .nojekyll ファイルの設置 ---
echo ".nojekyll ファイルを設置します (GitHub Pagesに静的サイトであることを伝えるため)。"
touch .nojekyll

# --- Step 1: index.html はユーザーが/var/www/html/publicに配置したものをそのまま利用 ---
echo "index.html は /var/www/html/public に配置されたものをそのまま利用します。"
if [ ! -f "index.html" ]; then
    echo "警告: index.html が /var/www/html/public に見つかりません。サイトのトップページが表示されない可能性があります。" >&2
fi

# --- Step 1.5: sitemap.xml の生成 ---
generate_sitemap # sitemap.xmlを生成

# --- Step 2: Gitデプロイ ---
echo "変更をコミットしてプッシュします..."
git add .

# git add . の後に、ステージングエリアに何か変更があるか確認する
if git diff --cached --quiet; then
    echo "変更はありません。デプロイをスキップします。"
else
    # コミットメッセージを引数で受け取るか、デフォルト値を使う
    COMMIT_MESSAGE="AI Business Homepage deployment on $(date)"
    if [ -n "$1" ]; then # 引数があればコミットメッセージにする
        COMMIT_MESSAGE="$1"
    fi

    git commit -m "$COMMIT_MESSAGE"
    git push -u origin main --force # 強制プッシュでリモートをローカルに合わせる
    echo "デプロイが完了しました！"
fi

echo "----------------------------------------"
echo "${HTML_SITE_ROOT} に数分後に反映されます。"
--- 処理完了 ---
