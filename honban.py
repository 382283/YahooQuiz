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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.ai_levels = {
            'strong': {
                'correct_rate': 0.95,  # 95%の正解率
                'reaction_time': {
                    'min': 6.0,        # 最速0.3秒
                    'max': 8.0         # 最長1秒
                }
            },
            'normal': {
                'correct_rate': 0.80,  # 80%の正解率
                'reaction_time': {
                    'min': 8.0,
                    'max': 11.0
                }
            },
            'weak': {
                'correct_rate': 0.60,  # 60%の正解率
                'reaction_time': {
                    'min': 10.0,
                    'max': 15.0
                }
            }
        }
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro', generation_config={
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40
        })

    def simulate_ai_buzzer(self, level='normal'):
        """AIの早押し判定をレベルに応じてシミュレート"""
        level_config = self.ai_levels[level]
        return random.uniform(
            level_config['reaction_time']['min'],
            level_config['reaction_time']['max']
        )

    def simulate_ai_answer(self, level='normal'):
        """AIの回答をレベルに応じてシミュレート"""
        return random.random() < self.ai_levels[level]['correct_rate']

    def get_ai_thinking_message(self, level='normal'):
        """AIの思考メッセージをレベルに応じて変更"""
        messages = {
            'strong': [
                "高精度で解析中...",
                "過去の記事と詳細な照合を実施中...",
                "複数のデータベースを並列検索中..."
            ],
            'normal': [
                "データを分析中...",
                "関連記事を確認中...",
                "情報を検索中..."
            ],
            'weak': [
                "なんとか思い出そうとしています...",
                "記事を読み返しています...",
                "ゆっくり考え中..."
            ]
        }
        return random.choice(messages[level])

    def get_news_article(self):
        """Yahoo!ニュースから記事を取得"""
        try:
            url = "https://news.yahoo.co.jp/topics/business"
            response = requests.get(url, headers=self.headers, timeout=10)  # タイムアウト追加
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_feed = soup.find('ul', class_='newsFeed_list')
            article_links = news_feed.find_all('a') if news_feed else []
            
            if article_links:
                random_article = random.choice(article_links)
                article_url = random_article.get('href')
                
                article_response = requests.get(article_url, headers=self.headers, timeout=10)
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                full_article_link = article_soup.find('a', {
                    'class': 'sc-gdv5m1-9 bxbqJP',
                    'data-ual-gotocontent': 'true'
                })
                
                if full_article_link:
                    full_url = full_article_link.get('href')
                    full_response = requests.get(full_url, headers=self.headers, timeout=10)
                    full_soup = BeautifulSoup(full_response.text, 'html.parser')
                    
                    article_content = full_soup.find('div', class_='article_body')
                    if article_content:
                    # 記事情報を辞書として返す
                        return {
                            'content': ' '.join([p.text.strip() for p in article_content.find_all(['p', 'h2'])]),
                            'url': full_url,
                            'title': full_soup.find('h1').text.strip() if full_soup.find('h1') else 'タイトルなし'
                        }
            
            return None
        except Exception as e:
            print(f"記事取得エラー: {e}")
            return None

    def generate_quiz(self, text):
        """AIによるクイズ生成"""
        try:
            prompt = f"""
以下の文章から時事ネタのクイズを作成してください。
1単語で答えられる問題にしてください。
以下のフォーマットで出力してください：

Question: （ここに問題文）
Answer: （ここに1単語で答え）
Explanation: （ここに解説）

文章:
{text}
"""
            response = self.model.generate_content(prompt)
            
            if response.text:
                lines = response.text.split('\n')
                quiz_data = {}
                
                for line in lines:
                    if line.startswith('Question:'):
                        quiz_data['question'] = line.replace('Question:', '').strip()
                    elif line.startswith('Answer:'):
                        quiz_data['answer'] = line.replace('Answer:', '').strip()
                    elif line.startswith('Explanation:'):
                        quiz_data['explanation'] = line.replace('Explanation:', '').strip()
                
                return quiz_data
                
            return None
        except Exception as e:
            print(f"クイズ生成エラー: {e}")
            return None


    def create_quiz(self):
        """記事取得からクイズ生成までの一連の処理"""
        article_data = self.get_news_article()
        if article_data:
            quiz_data = self.generate_quiz(article_data['content'])
            if quiz_data:
                # クイズデータに記事情報を追加
                quiz_data['article_content'] = article_data['content']
                quiz_data['article_url'] = article_data['url']
                quiz_data['article_title'] = article_data['title']
                return quiz_data
        return None