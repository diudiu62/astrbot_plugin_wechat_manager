'''
Author: diudiu62
Date: 2025-03-10 18:13:18
LastEditTime: 2025-03-12 14:51:01
'''
import asyncio
from astrbot.api import logger
import xml.etree.ElementTree as ET
from .base_manager import BaseManager


class SendMessage(BaseManager):

    async def send_welcome_message(self, to_username: str, message: str = None) -> None:
        """
        发送欢迎消息给新朋友。

        :param to_username: 收件人用户名
        """
        if message is None:
            message = self.accept_friend_config.get(
                "accept_friend_say_message", "")
        delay = int(self.accept_friend_config.get(
            "accept_friend_say_message_delay", 0))
        await asyncio.sleep(delay)
        logger.info(f"向用户【{to_username}】发送: {message}")
        self.client.post_text(self.appid, to_username, message)

    async def send_group_welcome_message(self, event) -> None:
        text = event.message_obj.raw_message['Content']['string']
        # notes_bot_join_group = ["邀请你", "invited you", "You've joined", "你通过扫描"]
        # if any(note_bot_join_group in text for note_bot_join_group in notes_bot_join_group):  # 邀请机器人加入群聊
        #     logger.debug("不处理机器人加入群聊消息。")
        #     pass
        sysmsgtemplate = text.find('.//sysmsgtemplate')
        if sysmsgtemplate:
            # 系统消息
            try:
                # 解析xml
                xml_text = text.split(':\n', 1) if ':\n' in text else text
                group_id = xml_text[0]
                mes_data = ET.fromstring(xml_text[1])

                invited_link = mes_data.find(
                    ".//link[@name='names']//username")
                invited_username = invited_link.text if invited_link is not None else "未知用户"
                # 邀请的用户nickname
                invited_link = mes_data.find(
                    ".//link[@name='names']//nickname")
                invited_nickname = invited_link.text if invited_link is not None else "未知用户"
                # 处理被remark的nickname
                if "_" in invited_nickname:
                    # 找到最后一个下划线的位置
                    last_underscore_index = invited_nickname.rfind("_")
                    # 获取最后一个下划线后面的部分
                    suffix = invited_nickname[last_underscore_index + 1:]
                    # 指定要去掉的关键字数组
                    keywords = self.accept_friend_config.get("keywords", [])
                    # 如果后缀在关键字数组中，去掉最后一个下划线及其后面的关键字
                    if suffix in keywords:
                        invited_nickname = invited_nickname[:last_underscore_index]

                welcome_msg = self.group_invitation_config.get(
                    "group_welcome_msg", "")
                if welcome_msg:
                    delay = int(self.group_invitation_config.get(
                        "group_welcome_msg_delay", 0))
                    await asyncio.sleep(delay)
                    if invited_nickname != "未知用户":
                        self.client.post_text(
                            self.appid, group_id, f'@{invited_nickname} {welcome_msg}', invited_username)
                        logger.info(f"发送入群欢迎消息: {welcome_msg}")

            except ET.ParseError as e:
                logger.error(f"[gewechat] Failed to parse group join XML: {e}")
                # Fall back to regular text handling
                pass
