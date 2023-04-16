import requests
from typing import TypedDict, Literal

from bs4 import BeautifulSoup
import openai
import streamlit

def get_body(url: str) -> str:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("article")
    if article is None:
        article = soup.find("body")
    return article.get_text() # type: ignore

class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str

class Chat:
    def __init__(
            self,
            prompts: list[ChatMessage] = [],
            model = 'gpt-3.5-turbo',
            stream=False
        ) -> None:
        self.prompts = prompts
        self.model = model
        self.stream = stream

    def create(self):
        return openai.ChatCompletion.create(
            model=self.model,
            messages=self.prompts,
            stream=self.stream,
        )


def summarize_chat(url: str, model):
    SYSTEM_PROMPT = """
    与える文章を3行以内で要約し、1行あけて一言だけ意見を述べてください。

    要約と意見の両方とも、ですます調で丁寧な表現を使って出力してください。
    すべての出力は日本語にしてください。
    """.strip()

    return Chat(
        model=model,
        prompts=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": get_body(url)}
        ],
        stream=True
    )

streamlit.title("記事要約")

model = streamlit.radio("モデル", ('gpt-3.5-turbo', 'gpt-4'), index=0)
input_url = streamlit.text_input('URL', placeholder='https://example.com')

if len(input_url) > 0:
    chat = summarize_chat(input_url, model)
    completion = chat.create()
    main_tab, prompt_tab = streamlit.tabs(["Result", "Prompt"])

    with main_tab:
        result_area = streamlit.empty()
        text = ''
        for chunk in completion:
            next: str = chunk['choices'][0]['delta'].get('content', '') # type: ignore
            text += next
            if "。" in next:
                text += "\n"
            result_area.write(text)

    with prompt_tab:
        streamlit.write(chat.prompts)
