import streamlit as st
from GoogleNews import GoogleNews
from newspaper import Article
import openai

# OpenAI API 키 입력
openai_api_key = "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"
client = openai.OpenAI(api_key=openai_api_key)

# ------------------ 함수 정의 ------------------

def get_news_links(query, max_results=3):
    googlenews = GoogleNews(lang='ko', region='KR')
    googlenews.set_period('1d')
    googlenews.search(query)
    results = googlenews.results()
    links = []
    for article in results[:max_results]:
        link = article['link'].split('&')[0]  # 불필요한 URL 파라미터 제거
        links.append(link)
    return links

def extract_news_texts(links):
    texts = []
    for url in links:
        try:
            article = Article(url, language='ko')
            article.download()
            article.parse()
            texts.append(article.text.strip())
        except:
            texts.append("")
    return texts

def analyze_sentiment_gpt(text):
    prompt = f"""다음 뉴스는 주가에 어떤 영향을 미칠까?
긍정 / 부정 / 중립 중 하나로 판단하고, 그 이유를 한 문장으로 설명해줘.

[뉴스 내용]
{text[:1500]}"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 금융 분석가야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"분석 실패: {e}"

def summarize_signal(results):
    pos, neg, neu = 0, 0, 0
    for r in results:
        if "긍정" in r:
            pos += 1
        elif "부정" in r:
            neg += 1
        elif "중립" in r:
            neu += 1

    if pos >= 2:
        return "🟢 매수"
    elif neg >= 2:
        return "🔴 매도"
    else:
        return "🟡 보류"

# ------------------ Streamlit UI ------------------

st.title("📰 뉴스 기반 주식 시그널러")

query = st.text_input("분석할 종목명을 입력하세요 (예: 현대건설)", "현대건설")
num_articles = st.slider("기사 개수 선택", 1, 5, 3)

if st.button("분석 시작"):
    with st.spinner("뉴스 수집 및 분석 중..."):
        links = get_news_links(query, max_results=num_articles)
        texts = extract_news_texts(links)
        results = [analyze_sentiment_gpt(text) for text in texts]
        signal = summarize_signal(results)

    st.subheader("📈 최종 매매 시그널:")
    st.markdown(f"## {signal}")

    st.subheader("🧠 뉴스별 GPT 판단")
    for i, (link, result) in enumerate(zip(links, results)):
        with st.expander(f"[{i+1}] 기사 보기"):
            st.write(f"🔗 [기사 링크]({link})")
            st.write(result)