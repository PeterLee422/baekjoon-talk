import os
import pandas as pd

from .recommender import Recommender
from .llm import LLM

class Session:
    def __init__(self, user_handle: str, recommendations: list[int], llm: LLM, conv_id: str, title: str, history: list = []) -> None:
        self.user_handle = user_handle
        self.llm = llm
        self.recommendations = recommendations
        self.title = title
        self.prev_msgs = []
        self.conv_id = conv_id

    def chat(self, message: str) -> str:
        text_response, speech_response, prev_msgs = self.llm.chat(message, self.prev_msgs, self.recommendations)
        self.prev_msgs = prev_msgs
        # print(self.prev_msgs)
        if not self.title:
            self.title = self.llm.get_session_title(message, speech_response)
        return text_response, speech_response

class LLMRec:
    def __init__(self, api_key: str, prev_msgs: list = []) -> None:
        self.prev_msgs = prev_msgs
        self.TOP_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_PATH = os.path.join(self.TOP_PATH, 'data')
        self.MODEL_PATH = os.path.join(self.TOP_PATH, 'saved')
        self.lightgcn_recommender = Recommender(self.DATA_PATH)
        self.multivae_recommender = Recommender(self.DATA_PATH)
        self.llm = LLM(api_key=api_key)
        self.problem_info = pd.read_csv(os.path.join(self.DATA_PATH, 'problem_info.csv'))
        self._load_model()

    def _load_model(self) -> None:
        lightgcn_model_path = os.path.join(self.MODEL_PATH, 'LightGCN_model.pth')
        multivae_model_path = os.path.join(self.MODEL_PATH, 'MultiVAE_model.pth')
        if not os.path.exists(lightgcn_model_path):
            raise FileNotFoundError(f"Model file not found at {lightgcn_model_path}. Please train the model first.")
        if not os.path.exists(multivae_model_path):
            raise FileNotFoundError(f"Model file not found at {multivae_model_path}. Please train the model first.")
        self.lightgcn_recommender.load_model(lightgcn_model_path, model_type='LightGCN')
        self.multivae_recommender.load_model(multivae_model_path, model_type='MultiVAE')

    def get_new_session(self, user_handle: str, conv_id: str, title: str) -> Session:
        rec_ids = self.multivae_recommender.recommend(user_handle)
        rec_df = self.problem_info.set_index('problemId', drop=True).loc[rec_ids].reset_index()
        session = Session(user_handle, rec_df, self.llm, conv_id, title, self.prev_msgs)
        return session
