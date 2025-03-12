'''
Author: diudiu62
Date: 2025-03-04 18:23:07
LastEditTime: 2025-03-12 14:50:40
'''
from astrbot.api import logger
import asyncio

from typing import Dict, List, Any
from .base_manager import BaseManager

class GroupManager(BaseManager):

    async def handle_group_invitation(self, event: Any) -> None:
        '''关键字邀请进群'''
        if self.group_invitation_config.get("switch", False):
            keys_values = self.parse_keywords(
                self.group_invitation_config["keywords"])
            wxid = event.get_sender_id()
            userinfo = self.client.get_brief_info(self.appid, [wxid])
            nickname = userinfo['data'][0]['nickName']
            for item, group_id in keys_values.items():
                if event.message_str == item:
                    result = await self.invite_to_group(event.get_sender_id(), group_id, nickname)
                    event.stop_event()
                    return wxid, result
        return None, None

    async def accept_friend_group_invitation(self, keyword: str, wxid: str, nickname: str) -> None:
        '''添加好友时触发备注的关键字邀请进群'''
        keys_values = self.parse_keywords(
            self.group_invitation_config["keywords"])
        group_id = keys_values.get(keyword)
        if group_id:
            result = await self.invite_to_group(wxid, group_id, nickname)
            return result

    async def invite_to_group(self, wxid: str, group_id: str, nickname: str = None) -> None:
        delay = int(self.group_invitation_config.get(
            "group_invitation_delay", 0))
        await asyncio.sleep(delay)
        group_id_with_chatroom = f"{group_id}@chatroom"
        logger.debug(f"邀请的群ID: {group_id_with_chatroom}")

        users_list = self.client.get_chatroom_member_list(
            self.appid, group_id_with_chatroom)
        logger.debug(users_list)

        chatroom_info = self.client.get_chatroom_info(
            self.appid, group_id_with_chatroom)

        if not await self.is_user_in_group(wxid, users_list["data"]["memberList"]):
            logger.info("用户不在群中，正在邀请……")
            self.client.invite_member(
                self.appid, wxid, group_id_with_chatroom, "")
            return f"🤖 已经邀请你进入群【{chatroom_info['data']['nickName']}】。"
        else:
            logger.info(
                f"【{nickname}】已经在群【{chatroom_info['data']['nickName']}】中。")
            return f"🤖 你已经在群【{chatroom_info['data']['nickName']}】中啦。"

    async def is_user_in_group(self, wxid: str, member_list: List[Dict[str, str]]) -> bool:
        return any(member["wxid"] == wxid for member in member_list)
