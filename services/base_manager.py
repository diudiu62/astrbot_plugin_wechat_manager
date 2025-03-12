'''
Author: diudiu62
Date: 2025-03-12 09:56:41
LastEditTime: 2025-03-12 14:51:30
'''
from typing import List, Dict
from ..gewechat_client import GewechatClient


class BaseManager:
    def __init__(self, base_url, appid, gewechat_token, config: dict):
        self.client = GewechatClient(base_url, gewechat_token)
        self.appid = appid
        self.accept_friend_config = config.accept_friend_config
        self.group_invitation_config = config.group_invitation_config

        self.base_url = base_url
        self.gewechat_token = gewechat_token
        self.config = config

    @staticmethod
    def parse_keywords(keywords: List[str]) -> Dict[str, str]:
        '''解析关键字配置为字典形式'''
        return {k: v for item in keywords for k, v in [item.split('#')]}
