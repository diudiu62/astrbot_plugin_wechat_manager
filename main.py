'''
Author: diudiu62
Date: 2025-02-19 15:35:18
LastEditTime: 2025-03-05 11:22:20
'''
import asyncio
import xml.etree.ElementTree as ET
from astrbot.api.event import AstrMessageEvent
from astrbot.api.event.filter import platform_adapter_type, command, PlatformAdapterType
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.platform.sources.gewechat.gewechat_event import GewechatPlatformEvent
from .friend_manager import FriendManager
from .group_manager import GroupManager

@register("accept_friend", "diudiu62", "好友审核", "1.0.0", "https://github.com/diudiu62/astrbot_plugin_accept_friend.git")
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

            message_type = event.message_obj.raw_message["MsgType"]
            if message_type == 37:
                await self._handle_friend_request(event, friend_manager, group_manager)
            else:
                await group_manager.handle_group_invitation(event)

            event.stop_event()

    def _create_friend_manager(self, client) -> FriendManager:
        return FriendManager(
            client,
            self.config.get("accept_friend_config", {}),
            self.config.get("group_invitation_config", [])
        )

    def _create_group_manager(self, client) -> GroupManager:
        return GroupManager(
            client,
            self.config.get("group_invitation_config", [])
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