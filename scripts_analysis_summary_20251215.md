# `/home/hirosi/my_gemini_project/scripts` ディレクトリのスクリプト分析サマリー (2025年12月15日)

このドキュメントは、`/home/hirosi/my_gemini_project/scripts` ディレクトリ内のシェルスクリプトおよびPythonスクリプトの詳細な分析結果をまとめたものです。これらのスクリプトは連携し、AIによるコンテンツ生成からGitHub Pagesへの自動デプロイまでを一貫して行う、高度なウェブサイト管理・コンテンツ生成システムを構成しています。

---

## 1. AIによるコンテンツ生成・編集

*   **`generate_ai_homepage.py`**:
    *   **目的:** Gemini APIを利用して、AIビジネス向けのホームページコンテンツをゼロから生成します。
    *   **機能:** ユーザーからのビジネス情報（目的、ターゲット顧客、サービス内容など）を基に、詳細なプロンプトを構築し、`gemini-2.5-flash`モデルに送信。生成されたHTMLの`<body>`部コンテンツを整形し、完全なHTMLファイルとして`/var/www/html/public/ai_business_homepage.html`に保存します。

*   **`brush_up_homepage.py`**:
    *   **目的:** Gemini APIを利用して、既存のHTMLファイルをユーザーの指示に基づいてブラッシュアップ（修正・改善）します。
    *   **機能:** 指定されたHTMLファイルを読み込み、ユーザーのブラッシュアップ指示と共にGemini API (`gemini-2.5-flash`) に送信。APIからの応答で元のHTMLファイルを上書きし、元のファイルはバックアップされます。

*   **`nws_writer.py`**:
    *   **目的:** 「ネオワールドサーガ」専用の執筆支援AIとして機能し、物語を生成します。
    *   **機能:** `~/neo_world_saga_collection/`内の背景資料（Markdownファイル）をユーザーが選択し、物語のプロット指示と共にGemini API (`gemini-2.5-flash`) に送信。生成された物語は、`~/neo_world_saga_collection/99_その他/`に新しいMarkdownファイルとして保存されます。物語の末尾は「余韻」を残す形で生成されます。

---

## 2. コンテンツの集約・更新

*   **`generate_master_saga.py`**:
    *   **目的:** 「ネオワールドサーガ」コレクション内の全てのMarkdownファイルを結合し、一つのHTMLページを生成します。
    *   **機能:** `~/neo_world_saga_collection/`以下の全Markdownファイルを検索・結合し、MarkdownをHTMLに変換。`template.html`をベースに、生成されたHTMLコンテンツとサイトタイトル、メタディスクリプションを組み込み、`/var/www/html/public/neo_world_saga.html`として保存します。

*   **`update_rich_index.py`**:
    *   **目的:** `/var/www/html/public/`内の他のHTMLファイルへのリンクを動的に`index.html`に追加・更新します。
    *   **機能:** `public`ディレクトリ内の`index.html`以外のHTMLファイルを検出し、`link_display_names.json`で定義された表示名（または自動生成された表示名）を使用してリンク一覧を生成。このリンク一覧を「その他のコンテンツ」セクションとして`index.html`に挿入または更新します。

*   **`update_blog.py`**:
    *   **目的:** `blog.html`に開発記録エントリを追記します。
    *   **機能:** ハードコードされたMarkdown形式の開発記録（GitHub Pagesデプロイのトラブルシューティングに関する詳細な内容）をHTMLに変換し、`/var/www/html/public/blog.html`内の適切な位置（通常はフッターの前）に挿入して更新します。

---

## 3. GitHub Pagesへのデプロイ

*   **`deploy_web_test_02.sh`**:
    *   **目的:** `/var/www/html/public` ディレクトリの内容を `h011145/hirosi-web-test-02` リポジトリのGitHub Pages (`gh-pages`ブランチ) へデプロイします。
    *   **機能:** `/var/www/html/public` に `cd` し、Gitリポジリを初期化/設定（リモートURL、`gh-pages`ブランチ）。`sitemap.xml`を自動生成し、全ての変更をコミット後、`gh-pages`ブランチへ**強制プッシュ**します。これにより、`public`ディレクトリのコンテンツが `https://h011145.github.io/hirosi-web-test-02` に公開されます。

*   **`deploy_ai_business_homepage.sh`**:
    *   **目的:** `/var/www/html/public/ai_business_homepage.html` ファイルのみを、`h011145/ai-business-homepage-experiment` リポジトリのGitHub Pages (`main`ブランチ) へデプロイします。
    *   **機能:** `/var/www/html/public` に `cd` し、Gitリポジリを初期化/設定（リモートURL、`main`ブランチ）。`.nojekyll`ファイルを作成し、`ai_business_homepage.html`を指すリダイレクト用の`index.html`を生成。`sitemap.xml`も生成し、関連ファイルのみをコミット後、`main`ブランチへ**強制プッシュ**します。

---

**総括:**

このシステムは、AIによる動的なコンテンツ生成（ビジネスホームページ、物語執筆）と、既存コンテンツの強化・集約（ブログ更新、目次生成）を組み合わせ、最終的にGitHub Pagesを通じてウェブサイトとして公開する一連のワークフローを自動化するものです。特に`deploy_web_test_02.sh`は、中心的なデプロイメントパイプラインとして機能しています。
