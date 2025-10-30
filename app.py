from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from datetime import datetime
from honban import QuizGenerator
from firebase_service import FirebaseService
import os
import time
from dotenv import load_dotenv
from pathlib import Path

# ✅ .envファイルを読み込み（app.pyと同階層）
env_path = Path(__file__).resolve().parent / ".env"
try:
    load_dotenv(dotenv_path=env_path)
    print("✅ .envファイルの読み込みに成功しました")
except Exception as e:
    print(f"⚠️ .envファイルの読み込みに失敗: {e}")


print(f"🔍 GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')[:12]}...")

# ✅ Flaskアプリ初期化
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")

# ✅ QuizGenerator初期化
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEYが設定されていません。HerokuのConfig Varsを確認してください。")
    quiz_generator = None
else:
    try:
        quiz_generator = QuizGenerator(api_key=api_key)
        print("✅ QuizGeneratorの初期化に成功しました")
    except Exception as e:
        print(f"❌ QuizGenerator初期化エラー: {e}")
        quiz_generator = None

# ✅ Firebaseサービス初期化
try:
    firebase_service = FirebaseService()
    print("✅ Firebase: サービス初期化成功")
except Exception as e:
    print(f"⚠️ Firebase初期化失敗: {e}")
    firebase_service = None


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
        session["game_start_time"] = time.time()  # ゲーム開始時刻を記録
        session["question_results"] = []  # 個別問題結果を保存するリスト
        return redirect(url_for("quiz"))
    return render_template("game.html")


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    """クイズページ"""
    if "round" not in session:
        return redirect(url_for("index"))

    ai_level = session.get("ai_level", "normal")

    if request.method == "GET":
        # 新しい問題の用意
        try:
            if quiz_generator is None:
                error_msg = "クイズ生成サービスが初期化されていません。GEMINI_API_KEY環境変数が正しく設定されているか確認してください。"
                print(f"クイズ生成失敗: quiz_generator is None")
                return render_template("error.html", error_message=error_msg), 500

            quiz_data = quiz_generator.create_quiz()
            if quiz_data:
                session["current_quiz"] = quiz_data
                session["ai_buzzer_time"] = quiz_generator.simulate_ai_buzzer(ai_level)
                ai_thinking = quiz_generator.get_ai_thinking_message(ai_level)
                return render_template(
                    "quiz.html",
                    question=quiz_data["question"],
                    choice_a=quiz_data["choice_a"],
                    choice_b=quiz_data["choice_b"],
                    choice_c=quiz_data["choice_c"],
                    choice_d=quiz_data["choice_d"],
                    article_content=quiz_data["article_content"],
                    article_url=quiz_data["article_url"],
                    article_title=quiz_data["article_title"],
                    round=session["round"] + 1,
                    total=session["total_rounds"],
                    ai_level=ai_level,
                    ai_thinking=ai_thinking,
                )
            else:
                # quiz_dataが取得できなかった場合のエラーハンドリング
                error_msg = "クイズの生成に失敗しました。APIキーが正しく設定されているか確認してください。"
                print(f"クイズ生成失敗: quiz_data is None")
                return render_template("error.html", error_message=error_msg), 500
        except Exception as e:
            error_msg = f"クイズの生成中にエラーが発生しました: {str(e)}"
            print(f"クイズ生成エラー: {e}")
            return render_template("error.html", error_message=error_msg), 500

    elif request.method == "POST":
        quiz_data = session.get("current_quiz", {})
        if not quiz_data:
            return redirect(url_for("index"))

        player_time = float(request.form.get("time", 999))
        ai_time = session.get("ai_buzzer_time", 999)

        # 変数を初期化
        result = None
        ai_thinking = None  # ここで初期化

        print("\n==== 回答判定開始 ====")
        print(f"プレイヤーの回答時間: {player_time:.2f}秒")
        print(f"AIの回答時間: {ai_time:.2f}秒")

        if player_time < ai_time:
            print("\n✨ プレイヤーが早押し成功！")
            user_answer = request.form.get("answer", "").strip().upper()
            correct_answer = quiz_data.get("answer", "").upper()

            print(f"問題: {quiz_data.get('question')}")
            print(f"プレイヤーの回答: {user_answer}")
            print(f"正解: {correct_answer}")

            if user_answer == correct_answer:
                session["score"]["player"] += 1
                result = "correct"
                result_type = "correct"
                print("\n🎉 正解！")
            else:
                result = "wrong"
                result_type = "wrong"
                print("\n❌ 不正解...")

            # 個別問題結果をFirebaseに保存
            firebase_service.save_individual_question_result(
                quiz_data,
                user_answer,
                correct_answer,
                player_time,
                ai_time,
                result_type,
                ai_level,
            )

            # プレイヤーが回答した場合のAIの思考メッセージ
            ai_thinking = "まだ考えていたのに..."

        else:
            print("\n🤖 AIが早押し成功！")
            ai_level = session.get("ai_level", "normal")
            ai_correct = quiz_generator.simulate_ai_answer(ai_level)
            ai_thinking = quiz_generator.get_ai_thinking_message(ai_level)

            print(f"問題: {quiz_data.get('question')}")
            print(f"正解: {quiz_data.get('answer')}")

            if ai_correct:
                result = "ai_correct"
                result_type = "ai_correct"
                session["score"]["ai"] += 1
                print("\n🎯 AIが正解！")
            else:
                result = "ai_wrong"
                result_type = "ai_wrong"
                print("\n😅 AIが不正解！")

            # AIが回答した場合もFirebaseに保存
            firebase_service.save_individual_question_result(
                quiz_data,
                "AI回答",
                quiz_data.get("answer", ""),
                player_time,
                ai_time,
                result_type,
                ai_level,
            )

        print(f"プレイヤーの得点: {session['score']['player']}点")
        print(f"AIの得点: {session['score']['ai']}点")

        print("\n==== ラウンド情報 ====")
        session["round"] += 1
        print(f"現在のラウンド: {session['round']}/{session['total_rounds']}")

        if session["round"] >= session["total_rounds"]:
            print("\n🏁 ゲーム終了！")
            return redirect(url_for("result"))

        # 必ず返り値を返す
        return render_template(
            "quiz.html",
            question=quiz_data["question"],
            choice_a=quiz_data["choice_a"],
            choice_b=quiz_data["choice_b"],
            choice_c=quiz_data["choice_c"],
            choice_d=quiz_data["choice_d"],
            answer=quiz_data["answer"],
            explanation=quiz_data.get("explanation", ""),
            result=result,
            ai_thinking=ai_thinking,  # 常に定義された状態で渡される
            round=session["round"],
            total=session["total_rounds"],
            ai_level=session.get("ai_level", "normal"),
        )


@app.route("/api/quiz", methods=["GET"])
def api_quiz():
    quiz_data = quiz_generator.create_quiz()
    if quiz_data:
        return jsonify(
            {
                "question": quiz_data["question"],
                "choice_a": quiz_data["choice_a"],
                "choice_b": quiz_data["choice_b"],
                "choice_c": quiz_data["choice_c"],
                "choice_d": quiz_data["choice_d"],
                "article_content": quiz_data["article_content"],
                "article_url": quiz_data["article_url"],
                "article_title": quiz_data["article_title"],
            }
        )
    else:
        return jsonify({"error": "クイズの生成に失敗しました。"}), 500


@app.route("/result")
def result():
    """結果表示ページ"""
    if "score" not in session:
        return redirect(url_for("index"))

    ai_level = session.get("ai_level", "normal")

    # ゲーム時間を計算
    game_duration = None
    if "game_start_time" in session:
        game_duration = round(time.time() - session["game_start_time"], 2)

    # 結果をFirebaseに保存（Firebase接続がある場合のみ）
    if firebase_service is not None:
        firebase_service.save_quiz_result(
            session["score"]["player"],
            session["score"]["ai"],
            session["total_rounds"],
            ai_level,
            game_duration,
        )

    return render_template(
        "result.html",
        player_score=session["score"]["player"],
        ai_score=session["score"]["ai"],
        total=session["total_rounds"],
        ai_level=ai_level,
        game_duration=game_duration,
    )


@app.route("/stats")
def stats():
    """統計情報ページ"""
    # Firebase接続がない場合はデフォルト値を返す
    if firebase_service is None:
        recent_results = []
        statistics = {
            "total_games": 0,
            "total_questions": 0,
            "player_wins": 0,
            "ai_wins": 0,
            "draws": 0,
            "average_player_score": 0,
            "average_ai_score": 0,
            "ai_level_distribution": {"strong": 0, "normal": 0, "weak": 0},
        }
    else:
        recent_results = firebase_service.get_recent_results(limit=20)
        statistics = firebase_service.get_statistics()

    return render_template(
        "stats.html", recent_results=recent_results, statistics=statistics
    )


@app.route("/api/recent-results")
def api_recent_results():
    """最近の結果をAPIで取得"""
    limit = request.args.get("limit", 10, type=int)
    results = firebase_service.get_recent_results(limit=limit)
    return jsonify(results)


@app.route("/api/statistics")
def api_statistics():
    """統計情報をAPIで取得"""
    stats = firebase_service.get_statistics()
    return jsonify(stats)


@app.errorhandler(405)
def method_not_allowed(error):
    """Method Not Allowed エラーのハンドリング"""
    return (
        render_template(
            "error.html", error_message="このページは正しい方法でアクセスしてください。"
        ),
        405,
    )


@app.errorhandler(404)
def not_found(error):
    """Not Found エラーのハンドリング"""
    return render_template("error.html", error_message="ページが見つかりません。"), 404


@app.errorhandler(500)
def internal_error(error):
    """Internal Server Error のハンドリング"""
    return (
        render_template(
            "error.html", error_message="サーバー内部エラーが発生しました。"
        ),
        500,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
