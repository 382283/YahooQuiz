# quiz_generator.py
import google.generativeai as genai
import random
import requests
from bs4 import BeautifulSoup
import os


class QuizGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.ai_levels = {
            "strong": {
                "correct_rate": 0.95,  # 95%の正解率
                "reaction_time": {"min": 6.0, "max": 8.0},  # 最速6秒  # 最長8秒
            },
            "normal": {
                "correct_rate": 0.80,  # 80%の正解率
                "reaction_time": {"min": 8.0, "max": 11.0},
            },
            "weak": {
                "correct_rate": 0.60,  # 60%の正解率
                "reaction_time": {"min": 10.0, "max": 15.0},
            },
        }
        genai.configure(api_key=self.api_key)

        # 複数のモデル名を試す
        model_names = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
            "gemini-1.0-pro",
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
            raise Exception("利用可能なGeminiモデルが見つかりませんでした")

    def simulate_ai_buzzer(self, level="normal"):
        """AIの早押し判定をレベルに応じてシミュレート"""
        level_config = self.ai_levels[level]
        return random.uniform(
            level_config["reaction_time"]["min"], level_config["reaction_time"]["max"]
        )

    def simulate_ai_answer(self, level="normal"):
        """AIの回答をレベルに応じてシミュレート"""
        return random.random() < self.ai_levels[level]["correct_rate"]

    def get_ai_thinking_message(self, level="normal"):
        """AIの思考メッセージをレベルに応じて変更"""
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

    def get_news_article(self):
        """サンプル記事を返す（Yahoo!ニュースが利用できない場合のフォールバック）"""
        # Yahoo!ニュースのスクレイピングが難しい場合のサンプルデータ
        sample_articles = [
            {
                "content": "日本銀行は本日、政策金利を0.1%引き上げることを発表しました。これは2年ぶりの利上げとなり、インフレ対策の一環として実施されます。市場関係者からは慎重な反応が見られており、今後の経済動向に注目が集まっています。",
                "url": "https://example.com/news1",
                "title": "日銀が2年ぶりの利上げを決定",
            },
            {
                "content": "東京都は2025年度から新しい環境税を導入することを発表しました。この税制は企業の二酸化炭素排出量に応じて課税され、環境保護の推進を図ります。対象となる企業は約1000社で、年間約500億円の税収を見込んでいます。",
                "url": "https://example.com/news2",
                "title": "東京都が新環境税を導入へ",
            },
            {
                "content": "大手自動車メーカーのトヨタ自動車は、2030年までに電気自動車の生産台数を年間350万台に増加させる計画を発表しました。これは現在の約10倍の規模となり、カーボンニュートラル実現に向けた取り組みの一環です。",
                "url": "https://example.com/news3",
                "title": "トヨタ、EV生産を大幅拡大へ",
            },
        ]

        try:
            # 実際のYahoo!ニュースからの取得を試行
            url = "https://news.yahoo.co.jp/topics/business"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            news_feed = soup.find("ul", class_="newsFeed_list")
            article_links = news_feed.find_all("a") if news_feed else []

            if article_links:
                random_article = random.choice(article_links)
                article_url = random_article.get("href")

                article_response = requests.get(
                    article_url, headers=self.headers, timeout=10
                )
                article_soup = BeautifulSoup(article_response.text, "html.parser")

                full_article_link = article_soup.find(
                    "a", {"class": "sc-gdv5m1-9 bxbqJP", "data-ual-gotocontent": "true"}
                )

                if full_article_link:
                    full_url = full_article_link.get("href")
                    full_response = requests.get(
                        full_url, headers=self.headers, timeout=10
                    )
                    full_soup = BeautifulSoup(full_response.text, "html.parser")

                    article_content = full_soup.find("div", class_="article_body")
                    if article_content:
                        content_text = " ".join(
                            [
                                p.text.strip()
                                for p in article_content.find_all(["p", "h2"])
                            ]
                        )
                        return {
                            "content": content_text[:2000],
                            "url": full_url,
                            "title": (
                                full_soup.find("h1").text.strip()
                                if full_soup.find("h1")
                                else "タイトルなし"
                            ),
                        }

            # Yahoo!ニュースからの取得に失敗した場合、サンプル記事を使用
            print("Yahoo!ニュースからの記事取得に失敗、サンプル記事を使用します")
            return random.choice(sample_articles)

        except Exception as e:
            print(f"記事取得エラー: {e} - サンプル記事を使用します")
            return random.choice(sample_articles)

    def generate_quiz(self, text):
        """AIによる4択クイズ生成"""
        try:
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

            if response.text:
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
                        quiz_data["explanation"] = line.replace(
                            "Explanation:", ""
                        ).strip()

                # 必要なフィールドが全て揃っているかチェック
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
                    return quiz_data
                else:
                    print(f"クイズデータ不完全: {quiz_data}")
                    return None

            return None
        except Exception as e:
            print(f"クイズ生成エラー: {e}")
            return None

    def create_quiz(self):
        """記事取得からクイズ生成までの一連の処理"""
        try:
            article_data = self.get_news_article()
            if article_data:
                quiz_data = self.generate_quiz(article_data["content"])
                if quiz_data:
                    # クイズデータに記事情報を追加
                    quiz_data["article_content"] = article_data["content"]
                    quiz_data["article_url"] = article_data["url"]
                    quiz_data["article_title"] = article_data["title"]
                    return quiz_data
            return None
        except Exception as e:
            print(f"クイズ作成エラー: {e}")
            return None
