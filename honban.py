import google.generativeai as genai
import random
import requests
from bs4 import BeautifulSoup
import os


class QuizGenerator:
    def __init__(self, api_key):
        self.api_key = api_key

        # APIキーの検証
        if not api_key or api_key == "dummy_key":
            print("警告: GEMINI_API_KEYが設定されていません")
            raise ValueError(
                "GEMINI_API_KEY環境変数が設定されていません。HerokuのConfig Varsで設定してください。"
            )

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.ai_levels = {
            "strong": {
                "correct_rate": 0.95,
                "reaction_time": {"min": 6.0, "max": 8.0},
            },
            "normal": {
                "correct_rate": 0.80,
                "reaction_time": {"min": 8.0, "max": 11.0},
            },
            "weak": {
                "correct_rate": 0.60,
                "reaction_time": {"min": 10.0, "max": 15.0},
            },
        }

        print(f"APIキーの最初の10文字: {api_key[:10]}...")
        genai.configure(api_key=self.api_key)

        # 利用可能なモデルを順に試す
        model_names = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest",
            "gemini-pro",
        ]

        self.model = None
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"成功: モデル '{model_name}' を使用します")
                break
            except Exception as e:
                print(f"モデル '{model_name}' の初期化に失敗: {e}")
                continue

        if self.model is None:
            raise Exception(
                "利用可能なGeminiモデルが見つかりませんでした。APIキーが正しいか確認してください。"
            )

    # --------------------------
    # AI動作シミュレーション関連
    # --------------------------
    def simulate_ai_buzzer(self, level="normal"):
        level_config = self.ai_levels[level]
        return random.uniform(
            level_config["reaction_time"]["min"], level_config["reaction_time"]["max"]
        )

    def simulate_ai_answer(self, level="normal"):
        return random.random() < self.ai_levels[level]["correct_rate"]

    def get_ai_thinking_message(self, level="normal"):
        messages = {
            "strong": [
                "高精度で解析中...",
                "過去の記事と詳細な照合を実施中...",
                "複数のデータベースを並列検索中...",
            ],
            "normal": ["データを分析中...", "関連記事を確認中...", "情報を検索中..."],
            "weak": [
                "なんとか思い出そうとしています...",
                "記事を読み返しています...",
                "ゆっくり考え中...",
            ],
        }
        return random.choice(messages[level])

    # --------------------------
    # 記事取得
    # --------------------------
    def get_news_article(self):
        sample_articles = [
            {
                "content": "日本銀行は本日、政策金利を0.1%引き上げることを発表しました。これは2年ぶりの利上げとなり、インフレ対策の一環として実施されます。",
                "url": "https://example.com/news1",
                "title": "日銀が2年ぶりの利上げを決定",
            },
            {
                "content": "東京都は2025年度から新しい環境税を導入することを発表しました。この税制は企業の二酸化炭素排出量に応じて課税されます。",
                "url": "https://example.com/news2",
                "title": "東京都が新環境税を導入へ",
            },
            {
                "content": "トヨタ自動車は、2030年までに電気自動車の生産台数を年間350万台に増加させる計画を発表しました。",
                "url": "https://example.com/news3",
                "title": "トヨタ、EV生産を大幅拡大へ",
            },
        ]

        try:
            url = "https://news.yahoo.co.jp/topics/business"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            news_feed = soup.find("ul", class_="newsFeed_list")
            article_links = news_feed.find_all("a") if news_feed else []

            if article_links:
                random_article = random.choice(article_links)
                article_url = random_article.get("href")
                article_response = requests.get(article_url, headers=self.headers, timeout=10)
                article_soup = BeautifulSoup(article_response.text, "html.parser")

                content = article_soup.get_text()[:2000]
                title = article_soup.find("h1").text if article_soup.find("h1") else "タイトルなし"

                return {"content": content, "url": article_url, "title": title}

            print("Yahoo!ニュースからの記事取得に失敗、サンプル記事を使用します")
            return random.choice(sample_articles)

        except Exception as e:
            print(f"記事取得エラー: {e} - サンプル記事を使用します")
            return random.choice(sample_articles)

    # --------------------------
    # クイズ生成
    # --------------------------
    def generate_quiz(self, text):
        """AIによる4択クイズ生成"""  # ←★ここ、インデント修正＋docstring正位置
        try:
            print("🧠 Gemini APIにリクエスト送信中...")
            prompt = f"""
以下の文章から時事ネタの4択クイズを作成してください。
以下のフォーマットで出力してください：

Question: （ここに問題文）
A: （選択肢A）
B: （選択肢B）
C: （選択肢C）
D: （選択肢D）
Answer: （正解の選択肢A、B、C、Dのいずれか）
Explanation: （ここに解説）

文章:
{text}
"""
            response = self.model.generate_content(prompt)

            print("🧩 Geminiのレスポンス受信完了")
            print("📩 生のレスポンス:")
            print(response.text if hasattr(response, "text") else response)

            if not hasattr(response, "text") or not response.text:
                print("❌ レスポンスにtextが含まれていません")
                return None

            lines = response.text.split("\n")
            quiz_data = {}

            for line in lines:
                line = line.strip()
                if line.startswith("Question:"):
                    quiz_data["question"] = line.replace("Question:", "").strip()
                elif line.startswith("A:"):
                    quiz_data["choice_a"] = line.replace("A:", "").strip()
                elif line.startswith("B:"):
                    quiz_data["choice_b"] = line.replace("B:", "").strip()
                elif line.startswith("C:"):
                    quiz_data["choice_c"] = line.replace("C:", "").strip()
                elif line.startswith("D:"):
                    quiz_data["choice_d"] = line.replace("D:", "").strip()
                elif line.startswith("Answer:"):
                    quiz_data["answer"] = line.replace("Answer:", "").strip()
                elif line.startswith("Explanation:"):
                    quiz_data["explanation"] = line.replace("Explanation:", "").strip()

            required_fields = [
                "question",
                "choice_a",
                "choice_b",
                "choice_c",
                "choice_d",
                "answer",
                "explanation",
            ]
            if all(key in quiz_data for key in required_fields):
                print("✅ クイズ生成成功！")
                return quiz_data
            else:
                print("⚠️ クイズデータ不完全:", quiz_data)
                return None

        except Exception as e:
            import traceback
            print("=== クイズ生成エラー詳細 ===")
            traceback.print_exc()
            print("=============================")
            return None

    # --------------------------
    # 記事取得＋クイズ生成
    # --------------------------
    def create_quiz(self):
        """記事取得からクイズ生成までの一連の処理"""
        try:
            article_data = self.get_news_article()
            if article_data:
                quiz_data = self.generate_quiz(article_data["content"])
                if quiz_data:
                    quiz_data["article_content"] = article_data["content"]
                    quiz_data["article_url"] = article_data["url"]
                    quiz_data["article_title"] = article_data["title"]
                    return quiz_data
            return None
        except Exception as e:
            print(f"クイズ作成エラー: {e}")
            return None
