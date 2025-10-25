from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")

@app.route("/", methods=["GET"])
def index():
    """トップページ"""
    return render_template("index.html")

@app.route("/game", methods=["GET", "POST"])
def game():
    """ゲーム開始ページ"""
    if request.method == "POST":
        # AIレベルの選択を受け取る
        ai_level = request.form.get("ai_level", "normal")
        session["ai_level"] = ai_level
        session["score"] = {"player": 0, "ai": 0}
        session["round"] = 0
        session["total_rounds"] = 5
        return redirect(url_for("quiz"))
    return render_template("game.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    """クイズページ"""
    if "round" not in session:
        return redirect(url_for("index"))
    
    if request.method == "GET":
        return render_template("quiz.html", 
                             question="テスト問題です",
                             choice_a="選択肢A",
                             choice_b="選択肢B", 
                             choice_c="選択肢C",
                             choice_d="選択肢D",
                             round=session["round"] + 1,
                             total=session["total_rounds"])
    
    elif request.method == "POST":
        session["round"] += 1
        if session["round"] >= session["total_rounds"]:
            return redirect(url_for("result"))
        return render_template("quiz.html",
                             question="テスト問題です",
                             choice_a="選択肢A",
                             choice_b="選択肢B",
                             choice_c="選択肢C", 
                             choice_d="選択肢D",
                             round=session["round"] + 1,
                             total=session["total_rounds"])

@app.route("/result")
def result():
    """結果表示ページ"""
    if "score" not in session:
        return redirect(url_for("index"))
    
    return render_template("result.html",
                          player_score=session["score"]["player"],
                          ai_score=session["score"]["ai"],
                          total=session["total_rounds"])

@app.route("/stats")
def stats():
    """統計情報ページ"""
    return render_template("stats.html", 
                         recent_results=[],
                         statistics={"total_games": 0})

@app.errorhandler(405)
def method_not_allowed(error):
    """Method Not Allowed エラーのハンドリング"""
    return "Method Not Allowed - このページは正しい方法でアクセスしてください。", 405

@app.errorhandler(404)
def not_found(error):
    """Not Found エラーのハンドリング"""
    return "Page Not Found - ページが見つかりません。", 404

@app.errorhandler(500)
def internal_error(error):
    """Internal Server Error のハンドリング"""
    return "Internal Server Error - サーバー内部エラーが発生しました。", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
