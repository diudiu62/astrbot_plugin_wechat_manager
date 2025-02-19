'''
Author: diudiu62
Date: 2025-02-17 10:10:26
LastEditTime: 2025-02-19 15:09:23
'''
import asyncio
import xml.etree.ElementTree as ET
from astrbot.api.event import AstrMessageEvent
from astrbot.api.event.filter import platform_adapter_type, PlatformAdapterType
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.platform.sources.gewechat.gewechat_event import GewechatPlatformEvent


@register("accept_friend", "diudiu62", "好友审核", "1.0.0", "repo url")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.accept_friend_commands = config.get("accept_friend_commands", {})
        self.accept_friend_is_say = config.get("accept_friend_is_say", {})

    @platform_adapter_type(PlatformAdapterType.GEWECHAT)
    async def accept_friend(self, event: AstrMessageEvent):
        '''个人微信好友审核管理'''
        if event.get_platform_name() == "gewechat":
            if event.message_obj.raw_message["MsgType"] == 37:
                logger.info("收到好友请求")
                content_xml = event.message_obj.raw_message["Content"]["string"]
                
                # 尝试解析 XML
                try:
                    content_xml = ET.fromstring(content_xml)
                    remark = content_xml.attrib.get('content')
                    fromnickname = content_xml.attrib.get('fromnickname')
                    fromusername = content_xml.attrib.get('fromusername')
                    v3 = content_xml.attrib.get('encryptusername')
                    v4 = content_xml.attrib.get('ticket')
                except ET.ParseError as e:
                    logger.error(f"解析好友请求内容时出错: {e}")
                    return
                    
                logger.info("friend request content: {}".format(remark))
                found_keyword = False

                keywords = self.accept_friend_commands.get("keywords", [])
                if not keywords:
                    logger.warning("没有定义关键词，无法处理好友请求。")
                    return
                
                for keyword in keywords:
                    logger.debug(f"keyword: {keyword}")
                    if keyword in remark:
                        found_keyword = True
                        await asyncio.sleep(3)  # 延时

                        logger.info(f"{fromnickname} 通过验证！（{keyword}）")
                        assert isinstance(event, GewechatPlatformEvent)
                        client = event.client
                        
                        # 同意添加好友
                        try:
                            delay = self.accept_friend_commands.get("delay", 0)
                            await asyncio.sleep(delay)  # 延时
                            await client.add_contacts(3, 3, v3, v4, remark)
                            logger.info(f"同意添加好友: {fromnickname}")
                        except Exception as e:
                            logger.error(f"添加好友失败: {e}")
                            return

                        # 发送欢迎消息
                        if self.accept_friend_is_say.get("switch", False):
                            await self.send_welcome_message(client, fromusername)
                        break

                if not found_keyword:
                    logger.info(f"{fromnickname} 好友请求待审核。")

    async def send_welcome_message(self, client, to_username):
        """发送欢迎消息"""
        message = self.accept_friend_is_say.get("message", "🤖 很高兴认识你！🌹")
        delay = self.accept_friend_is_say.get("delay", 0)
        await asyncio.sleep(delay)  # 延时
        logger.info(f"发送: {message}")
        await client.post_text(to_username, message)