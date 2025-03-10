'''
Author: diudiu62
Date: 2025-02-19 15:35:18
LastEditTime: 2025-03-05 13:53:20
'''
import xml.etree.ElementTree as ET
from astrbot.api.event import AstrMessageEvent
from astrbot.api.event.filter import platform_adapter_type, command, PlatformAdapterType
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.platform.sources.gewechat.gewechat_event import GewechatPlatformEvent
from .friend_manager import FriendManager
from .group_manager import GroupManager
from .send_welcome_message import SendMessage


@register("accept_friend", "diudiu62", "好友审核&邀请进群", "1.0.0", "https://github.com/diudiu62/astrbot_plugin_accept_friend.git")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        

    @command("groupid")
    async def get_group_id(self, event: AstrMessageEvent) -> None:
        groupid = event.get_group_id().split('@')[0]
        await event.plain_result(f"当前群ID：{groupid}")
        event.stop_event()

    @platform_adapter_type(PlatformAdapterType.GEWECHAT)
    async def accept_friend(self, event: AstrMessageEvent) -> None:
        if event.get_platform_name() == "gewechat":
            assert isinstance(event, GewechatPlatformEvent)
            client = event.client

            friend_manager = self._create_friend_manager(client)
            group_manager = self._create_group_manager(client)
            is_group = True if "@chatroom" in event.message_obj.raw_message['FromUserName']['string'] else False

            message_type = event.message_obj.raw_message["MsgType"]
            if message_type == 37:
                # 好友申请
                await self._handle_friend_request(event, friend_manager, group_manager)
                event.stop_event()
            elif message_type == 10002 and is_group:
                # 有邀请入群消息
                send_message = SendMessage(self.config.get("group_invitation_config", {}))
                await send_message.send_group_welcome_message(client, event)
            else:
                # 其他处理
                await group_manager.handle_group_invitation(event)



    def _create_friend_manager(self, client) -> FriendManager:
        return FriendManager(
            client,
            self.config.get("accept_friend_config", {}),
            self.config.get("group_invitation_config", {})
        )

    def _create_group_manager(self, client) -> GroupManager:
        return GroupManager(
            client,
            self.config.get("group_invitation_config", {})
        )

    async def _handle_friend_request(self, event: AstrMessageEvent, friend_manager: FriendManager, group_manager: GroupManager) -> None:
        content_xml = event.message_obj.raw_message.get("Content", {}).get("string", "")

        try:
            content_xml = ET.fromstring(content_xml)
            remark = content_xml.attrib.get('content')
            fromnickname = content_xml.attrib.get('fromnickname')
            fromusername = content_xml.attrib.get('fromusername')
            v3 = content_xml.attrib.get('encryptusername')
            v4 = content_xml.attrib.get('ticket')

            data, result, userinfo = await friend_manager.accept_friend_request(v3, v4, remark, fromnickname, fromusername)
            if data == "group_invite" and result:
                await group_manager.accept_friend_group_invitation(userinfo['keyword'], userinfo['wxid'], userinfo['nickname'])
        except ET.ParseError as e:
            logger.error(f"Error parsing friend request content: {e}")