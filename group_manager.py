'''
Author: diudiu62
Date: 2025-03-04 18:23:07
LastEditTime: 2025-03-05 11:55:21
'''
from astrbot.api import logger
import asyncio
from typing import Dict, List, Any

class GroupManager:
    def __init__(self, client: Any, config: Dict[str, Any]) -> None:
        self.client = client
        self.config = config

    async def handle_group_invitation(self, event: Any) -> None:
        '''关键字邀请进群'''
        if self.config.get("switch", False):
            keys_values = self.parse_keywords(self.config["keywords"])
            wxid = event.get_sender_id()
            userinfo = await self.client.get_brief_info([wxid])
            nickname = userinfo['data'][0]['nickName']
            for item, group_id in keys_values.items():
                if event.message_str == item:
                    await self.invite_to_group(event.get_sender_id(), group_id, nickname)
                    break

    async def accept_friend_group_invitation(self, keyword: str, wxid: str, nickname: str) -> None:
        '''添加好友时触发备注的关键字邀请进群'''
        keys_values = self.parse_keywords(self.config["keywords"])
        group_id = keys_values.get(keyword)
        if group_id:
            await self.invite_to_group(wxid, group_id, nickname)

    async def invite_to_group(self, wxid: str, group_id: str, nickname: str = None) -> None:
        delay = int(self.config.get("group_invitation_delay", 0))
        await asyncio.sleep(delay)
        group_id_with_chatroom = f"{group_id}@chatroom"
        logger.debug(f"邀请的群ID: {group_id_with_chatroom}")

        users_list = await self.client.get_chatroom_member_list(group_id_with_chatroom)
        logger.debug(users_list)

        if not await self.is_user_in_group(wxid, users_list["data"]["memberList"]):
            logger.info("用户不在群中，正在邀请……")
            result = await self.client.invite_member(wxid, group_id_with_chatroom, "")
            if result['ret'] == 200:
                await self.send_group_welcome_message(wxid, nickname, group_id_with_chatroom)
        else:
            logger.info(f"【{nickname}】已经在群【{group_id_with_chatroom}】中。")

    @staticmethod
    def parse_keywords(keywords: List[str]) -> Dict[str, str]:
        '''解析关键字配置为字典形式'''
        return {k: v for item in keywords for k, v in [item.split('#')]}

    async def is_user_in_group(self, wxid: str, member_list: List[Dict[str, str]]) -> bool:
        return any(member["wxid"] == wxid for member in member_list)

    async def send_group_welcome_message(self, wxid: str, nickname: str, group_id: str) -> None:
        welcome_msg = self.config.get("group_welcome_msg", "")
        if welcome_msg:
            delay = int(self.config.get("group_welcome_msg_delay", 0))
            await asyncio.sleep(delay)
            await self.client.post_text(group_id, f'@{nickname} {welcome_msg}', wxid)
            logger.info(f"发送入群欢迎消息: {welcome_msg}")