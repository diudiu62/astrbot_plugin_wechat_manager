'''
Author: diudiu62
Date: 2025-03-10 18:13:18
LastEditTime: 2025-03-11 12:55:23
'''
import asyncio
from astrbot.api import logger
import xml.etree.ElementTree as ET
from ..gewechat_client import GewechatClient


class SendMessage:
    def __init__(self, base_url, appid, gewechat_token, config: dict):
        """
        初始化 FriendManager 实例。

        :param base_url: gewechat地址
        :param appid: 已登录的appid
        :param config: 配置信息
        """
        self.accept_friend_config = config.accept_friend_config
        self.group_invitation_config = config.group_invitation_config
        self.client = GewechatClient(base_url, gewechat_token)
        self.appid = appid

        
    async def send_welcome_message(self, to_username: str, message: str = None) -> None:
        """
        发送欢迎消息给新朋友。

        :param to_username: 收件人用户名
        """
        if message is None:
            message = self.accept_friend_config.get("accept_friend_say_message", "")
        delay = int(self.accept_friend_config.get("accept_friend_say_message_delay", 0))
        await asyncio.sleep(delay)
        logger.info(f"发送: {message}")
        self.client.post_text(self.appid, to_username, message)

    async def send_group_welcome_message(self, event) -> None:
        text = event.message_obj.raw_message['Content']['string']
        # notes_bot_join_group = ["邀请你", "invited you", "You've joined", "你通过扫描"]
        # if any(note_bot_join_group in text for note_bot_join_group in notes_bot_join_group):  # 邀请机器人加入群聊
        #     logger.debug("不处理机器人加入群聊消息。")
        #     pass
        try:
            # 解析xml
            xml_text = text.split(':\n', 1) if ':\n' in text else text
            group_id = xml_text[0]
            mes_data = ET.fromstring(xml_text[1])
            
            invited_link = mes_data.find(".//link[@name='names']//username")
            invited_username = invited_link.text if invited_link is not None else "未知用户"
            # 邀请的用户nickname
            invited_link = mes_data.find(".//link[@name='names']//nickname")
            invited_nickname = invited_link.text if invited_link is not None else "未知用户"

            welcome_msg = self.group_invitation_config.get("group_welcome_msg", "")
            if welcome_msg:
                delay = int(self.group_invitation_config.get("group_welcome_msg_delay", 0))
                await asyncio.sleep(delay)
                self.client.post_text(self.appid, group_id, f'@{invited_nickname} {welcome_msg}', invited_username)
                logger.info(f"发送入群欢迎消息: {welcome_msg}")

            return

        except ET.ParseError as e:
            logger.error(f"[gewechat] Failed to parse group join XML: {e}")
            # Fall back to regular text handling
            pass
    