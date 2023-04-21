import requests
from typing import TypedDict, Literal

from bs4 import BeautifulSoup
import openai
import streamlit

MODELS = ('gpt-3.5-turbo', 'gpt-4')

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

def stream_write(chunks, key=None):
    result_area = streamlit.empty()
    text = ''
    for chunk in chunks:
        next: str = chunk['choices'][0]['delta'].get('content', '') # type: ignore
        text += next
        if "。" in next:
            text += "\n"
        result_area.write(text, key=key)
    return text

sidebar = streamlit.sidebar.selectbox("Select Mode", ("要約", "チャット"))

if sidebar == "要約":
    streamlit.title("記事要約")

    model = streamlit.radio("モデル", MODELS, index=0)
    input_url = streamlit.text_input('URL', placeholder='https://example.com')

    if len(input_url) > 0:
        chat = summarize_chat(input_url, model)
        completion = chat.create()
        main_tab, prompt_tab = streamlit.tabs(["Result", "Prompt"])

        with main_tab:
            stream_write(completion)
        with prompt_tab:
            streamlit.write(chat.prompts)

elif sidebar == "チャット":
    prompts: list[ChatMessage] = []
    model = streamlit.radio("モデル", MODELS, index=0)
    if model is None:
        streamlit.stop()
    chat_widget = streamlit.empty()

    @streamlit.cache_data
    def cached_chat(prompts):
        chat = Chat(
            model=model,
            prompts=prompts,
            stream=True
        )
        completion = chat.create()
        text = stream_write(completion, key=f'output_{prompts}')
        return text

    while True:
        with chat_widget.container():
            for prompt in prompts:
                streamlit.write(prompt['content'])
            input_text = streamlit.text_input('入力', key=f'input_{prompts}')
            if len(input_text) == 0:
                streamlit.stop()
            prompts.append({"role": "user", "content": input_text})
            text = cached_chat(prompts)
            prompts.append({"role": "assistant", "content": text})
