from langchain_community.chat_models import ChatOpenAI

class ChatOpenRouter(ChatOpenAI):
    openai_api_base: str
    openai_api_key: str
    model_name: str

    def __init__(self,
                 model_name: str,
                 openai_api_key: str=None,
                 openai_api_base: str = "https://openrouter.ai/api/v1",
                 **kwargs):
        openai_api_key = "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"
        super().__init__(openai_api_base=openai_api_base,
                         openai_api_key=openai_api_key,
                         model_name=model_name, **kwargs)