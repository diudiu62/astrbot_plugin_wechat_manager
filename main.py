'''
Author: diudiu62
Date: 2025-02-19 15:35:18
:LastEditTime: 2025-03-18
'''
from astrbot.api.event import AstrMessageEvent
from astrbot.api.event.filter import platform_adapter_type, command, PlatformAdapterType
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.platform.sources.gewechat.gewechat_event import GewechatPlatformEvent
from .services.friend_manager import FriendManager
from .services.group_manager import GroupManager
from .services.send_welcome_message import SendMessage


@register("wechat_manager", "diudiu62", "微信社交管理", "1.1.4", "https://github.com/diudiu62/astrbot_plugin_wechat_manager.git")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.base_url = None
        self.appid = None
        self.gewechat_token = None

    @command("groupid")
    async def get_group_id(self, event: AstrMessageEvent) -> None:
        '''获取当前群聊groupid'''
        groupid = event.get_group_id().split('@')[0]
        await event.plain_result(f"当前群ID：{groupid}")
        event.stop_event()

    @platform_adapter_type(PlatformAdapterType.GEWECHAT)
    async def wechat_manager(self, event: AstrMessageEvent) -> None:
        '''监听微信消息，响应对应的行为策略'''
        if event.get_platform_name() != "gewechat":
            return
        assert isinstance(event, GewechatPlatformEvent)
        self.gewechat_token = event.client.token
        self.base_url = event.client.base_url
        self.appid = event.client.appid

        friend_manager = await self._create_friend_manager()
        group_manager = await self._create_group_manager()
        message_manager = await self._create_message_manager()

        message = None
        wxid = event.get_sender_id()
        MsgType = event.message_obj.raw_message
        match MsgType["MsgType"]:
            case 37:
                # 好友申请
                wxid, message = await friend_manager.accept_friend_request(event)
                event.stop_event()
            case 10002:
                # 有邀请入群消息
                await message_manager.send_group_welcome_message(event)
            case _:
                # 其他处理
                wxid, message = await group_manager.handle_group_invitation(event)
        if wxid != "weixin" and wxid and event.is_private_chat():
            # 好友类型用户才可以发私信
            await message_manager.send_welcome_message(wxid, message)

    async def _create_friend_manager(self) -> FriendManager:
        return FriendManager(
            self.base_url,
            self.appid,
            self.gewechat_token,
            self.config
        )

    async def _create_group_manager(self) -> GroupManager:
        return GroupManager(
            self.base_url,
            self.appid,
            self.gewechat_token,
            self.config
        )

    async def _create_message_manager(self) -> SendMessage:
        return SendMessage(
            self.base_url,
            self.appid,
            self.gewechat_token,
            self.config
        )
