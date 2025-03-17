import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import random
import time




def scrape_text(url):
    """指定されたURLからテキストをスクレイピングする関数"""
    try:
        print("\n==== 初期ページアクセス開始 ====")
        print(f"アクセスURL: {url}")
        
        # 最初のページにアクセス
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://news.yahoo.co.jp/'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("初期ページアクセス成功")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 記事のリンクを取得する部分を修正
        print("\n==== 記事リンク取得結果 ====")
        # newsFeed_list クラスの ul 内にある a タグを取得
        news_feed = soup.find('ul', class_='newsFeed_list')
        if news_feed:
            article_links = news_feed.find_all('a')
            print(f"取得した記事リンク数: {len(article_links)}")
            print("最初の3つのリンク:")
            for i, link in enumerate(article_links[:3]):
                print(f"{i+1}. {link.get('href')} - {link.text.strip()}")
        else:
            print("newsFeed_list クラスの ul タグが見つかりませんでした")
        
        if not article_links:
            raise Exception("記事のリンクが見つかりませんでした")
        
        # ランダムで1つの記事リンクを選択
        random_article = random.choice(article_links)
        article_url = random_article.get('href')
        print(f"\n==== 選択された記事 ====")
        print(f"URL: {article_url}")
        print(f"タイトル: {random_article.text.strip()}")
        
        # 相対URLの場合は絶対URLに変換
        if not article_url.startswith('http'):
            article_url = requests.compat.urljoin(url, article_url)
            print(f"絶対URLに変換: {article_url}")
        
        # 選択した記事ページにアクセス
        print("\n==== 記事ページアクセス ====")
        article_response = requests.get(article_url, headers=headers)
        article_response.raise_for_status()
        print("記事ページアクセス成功")
        
        article_soup = BeautifulSoup(article_response.text, 'html.parser')
        
        # 「記事全文を読む」リンクを探す
        print("\n==== 記事全文リンクの検索 ====")
        full_article_link = article_soup.find('a', {
            'class': 'sc-gdv5m1-9 bxbqJP',
            'data-ual-gotocontent': 'true'
        })
        
        print("「記事全文を読む」リンク検索結果:")
        if full_article_link:
            print(f"クラス: {full_article_link.get('class')}")
            print(f"href: {full_article_link.get('href')}")
            print(f"テキスト: {full_article_link.text}")
        else:
            print("リンクが見つかりませんでした")
            # HTML構造の確認
            print("\n記事ページのaタグ一覧（最初の5個）:")
            for a in article_soup.find_all('a')[:5]:
                print(f"クラス: {a.get('class')}, テキスト: {a.text.strip()}")
        
        if full_article_link:
            full_article_url = full_article_link.get('href')
            print(f"\n==== 記事全文ページアクセス ====")
            print(f"URL: {full_article_url}")
            
            # 記事全文ページにアクセス
            full_article_response = requests.get(full_article_url, headers=headers)
            full_article_response.raise_for_status()
            print("記事全文ページアクセス成功")
            
            full_article_soup = BeautifulSoup(full_article_response.text, 'html.parser')
            
            # 記事本文を抽出
            print("\n==== 記事本文の抽出 ====")
            article_content = full_article_soup.find('div', class_='article_body')
            
            if article_content:
                paragraphs = article_content.find_all(['p', 'h2'])
                print(f"段落数: {len(paragraphs)}")
                
                # 各段落の冒頭を表示
                print("\n最初の3つの段落:")
                for i, p in enumerate(paragraphs[:3]):
                    print(f"{i+1}. {p.text[:50]}...")
                
                # 本文のテキストを取得
                text_content = ' '.join([p.text.strip() for p in paragraphs if p.text.strip()])
                print(f"\n取得したテキストの長さ: {len(text_content)}文字")
                print(f"テキスト冒頭: {text_content[:200]}...")
                
                return text_content
            else:
                print("記事本文(article_body)が見つかりませんでした")
                print("\n利用可能なdivクラス一覧（最初の5個）:")
                for div in full_article_soup.find_all('div', class_=True)[:5]:
                    print(f"クラス: {div.get('class')}")
                raise Exception("記事本文が見つかりませんでした")
        else:
            raise Exception("記事全文リンクが見つかりませんでした")
            
    except Exception as e:
        print(f"\n==== エラー発生 ====")
        print(f"エラー内容: {str(e)}")
        return None



def generate_quiz(text):
    """Gemini APIを使用してクイズを生成する関数"""
    try:
        # APIの設定
        genai.configure(api_key='AIzaSyApCo7OjE2C4rDc00lmhreYTGbFvGfpsTQ')
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
以下の文章から時事ネタのクイズを1つ作成してください。
以下のフォーマットで出力してください：

Question: （ここに問題文）
Answer: （ここに1単語で答え）

文章:
{text}
"""
        
        response = model.generate_content(prompt)
        
        if response.text:
            # レスポンスを問題と答えに分割
            response_text = response.text
            question = ""
            answer = ""
            
            # Question: とAnswer: の行を探す
            for line in response_text.split('\n'):
                if line.startswith('Question:'):
                    question = line.replace('Question:', '').strip()
                elif line.startswith('Answer:'):
                    answer = line.replace('Answer:', '').strip()
            
            print("\n==== 生成されたクイズ ====")
            print(f"問題: {question}")
            print(f"答え: {answer}")
            
            return question, answer
        else:
            print("クイズを生成できませんでした")
            return None, None
            
    except Exception as e:
        print(f"\n==== Gemini API エラー ====")
        print(f"エラー内容: {str(e)}")
        return None, None

# メイン処理での使用例
def main():
    url = "https://news.yahoo.co.jp/topics/business"
    print("スクレイピング開始")
    
    text = scrape_text(url)
    
    if text:
        print("\n==== スクレイピング成功 ====")
        try:
            print("\n==== クイズ生成開始 ====")
            question, answer = generate_quiz(text)
            
            if question and answer:
                # 問題と答えを別々の変数として使用可能
                print("\n==== クイズの利用例 ====")
                print(f"生成された問題: {question}")
                print(f"生成された答え: {answer}")
            else:
                print("クイズの生成に失敗しました")
        except Exception as e:
            print(f"クイズ生成エラー: {str(e)}")
    else:
        print("\nスクレイピングに失敗しました")

if __name__ == "__main__":
    main()