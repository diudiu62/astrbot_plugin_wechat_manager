import asyncio
from astrbot.api import logger
import xml.etree.ElementTree as ET


class SendMessage:
    def __init__(self, config):
        self.config = config
        
    async def send_welcome_message(self, client, to_username: str, message: str = None) -> None:
        """
        发送欢迎消息给新朋友。

        :param to_username: 收件人用户名
        """
        if message is None:
            message = self.config.get("accept_friend_say_message", "")
        delay = int(self.config.get("accept_friend_say_message_delay", 0))
        await asyncio.sleep(delay)
        logger.info(f"发送: {message}")
        await client.post_text(to_username, message)

    async def send_group_welcome_message(self, client, event) -> None:
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

            welcome_msg = self.config.get("group_welcome_msg", "")
            if welcome_msg:
                delay = int(self.config.get("group_welcome_msg_delay", 0))
                await asyncio.sleep(delay)
                await client.post_text(group_id, f'@{invited_nickname} {welcome_msg}', invited_username)
                logger.info(f"发送入群欢迎消息: {welcome_msg}")

            return

        except ET.ParseError as e:
            logger.error(f"[gewechat] Failed to parse group join XML: {e}")
            # Fall back to regular text handling
            pass
    