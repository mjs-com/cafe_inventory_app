import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

# データベースファイルのパス
DATABASE = 'cafe_management.db'

# Flaskアプリケーションの初期化
app = Flask(__name__)
# 外部キー制約を有効にするための設定
# SQLiteはデフォルトでは外部キー制約を無視するため、接続時に有効化が必要です。
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 # 60 minutes for session timeout

# データベース接続を取得する関数
def get_db():
    # gはFlaskが提供する、リクエスト単位でデータを保存するオブジェクト
    db = getattr(g, '_database', None)
    if db is None:
        # データベースに接続
        db = g._database = sqlite3.connect(DATABASE)
        # SQLiteで外部キー制約を有効化する
        db.execute('PRAGMA foreign_keys = ON')
        # 結果を辞書形式で取得できるように設定（重要！）
        db.row_factory = sqlite3.Row
    return db

# アプリケーションコンテキストが終了する際にDB接続を閉じる
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# SQLを実行する汎用関数
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    # one=Trueの場合は結果の最初の行のみを返す（単一レコード取得用）
    return (rv[0] if rv else None) if one else rv

# --- ルーティング定義 ---

# トップページ：品目一覧表示と新規登録フォーム
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # --- 品目登録処理 ---
        item_name = request.form['item_name']
        unit = request.form['unit']
        min_stock = request.form.get('min_stock', 0) # min_stockが未入力なら0とする

        try:
            db = get_db()
            db.execute(
                'INSERT INTO items (item_name, unit, min_stock) VALUES (?, ?, ?)',
                [item_name, unit, min_stock]
            )
            db.commit() # 変更をデータベースに保存（重要！）
            # 登録成功後、トップページにリダイレクトして一覧を更新
            return redirect(url_for('index'))

        except sqlite3.Error as e:
            print(f"データベースエラーが発生しました: {e}")
            # エラー処理を実装する場合はここでメッセージを表示するなど
            return render_template('index.html', error_message="品目の登録中にエラーが発生しました。", items=query_db('SELECT * FROM items'))

    # --- 品目一覧表示処理 ---
    # itemsテーブルから全件取得
    items = query_db('SELECT * FROM items')
    
    # テンプレートをレンダリングして表示
    return render_template('index.html', items=items)

if __name__ == '__main__':
    # デバッグモードを有効にしてアプリケーションを実行
    app.run(debug=True)