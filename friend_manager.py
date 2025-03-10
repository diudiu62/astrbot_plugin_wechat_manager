'''
Author: diudiu62
Date: 2025-03-04 18:23:22
LastEditTime: 2025-03-05 11:49:44
'''
import asyncio
from astrbot.api import logger
from .send_welcome_message import SendMessage

class FriendManager:
    def __init__(self, client, accept_friend_config: dict, group_invitation_config: dict):
        """
        初始化 FriendManager 实例。

        :param client: 机器人客户端
        :param accept_friend_config: 好友请求接受配置
        :param group_invitation_config: 群邀请配置
        """
        self.client = client
        self.accept_friend_config = accept_friend_config
        self.group_invitation_config = group_invitation_config
        self.send_message = SendMessage(group_invitation_config)

    async def accept_friend_request(self, v3: str, v4: str, remark: str, 
                                     fromnickname: str, fromusername: str) -> tuple:
        """
        处理好友请求，检查是否包含关键词并做出相应的操作。

        :param v3: 友元 v3 信息
        :param v4: 友元 v4 信息
        :param remark: 申请备注
        :param fromnickname: 申请者昵称
        :param fromusername: 申请者用户名
        :return: ((str, bool, dict) | None) 返回群邀请结果或 None
        """
        logger.info("Incoming friend request: {}".format(remark))

        keywords = self.accept_friend_config.get("keywords", [])
        if not keywords:
            logger.warning("没有设置关键词，无法审核好友。")
            return None, None, None 

        for keyword in keywords:
            if keyword in remark:
                return await self.process_friend_request(v3, v4, remark, fromnickname, fromusername, keyword)

        logger.info(f"{fromnickname} ：好友申请待审核.")
        return None, False, {} 

    async def process_friend_request(self, v3: str, v4: str, remark: str, 
                                      fromnickname: str, fromusername: str, 
                                      keyword: str) -> tuple:
        """
        处理好友请求的具体逻辑，包括添加好友、重命名及发送欢迎消息。

        :param v3: 友元 v3 信息
        :param v4: 友元 v4 信息
        :param remark: 申请备注
        :param fromnickname: 申请者昵称
        :param fromusername: 申请者用户名
        :param keyword: 触发的关键词
        :return: ((str, bool, dict) | None) 返回群邀请结果或 None
        """
        logger.info(f"{fromnickname} 申请好友触发关键词： ({keyword})")
        delay = int(self.accept_friend_config.get("accept_friend_delay", 0))
        await asyncio.sleep(delay)
        await self.client.add_contacts(3, 3, v3, v4, remark)
        logger.info(f"Friend added: {fromnickname}")
        await asyncio.sleep(2)

        if self.accept_friend_config.get("rename", False):
            await self.rename_friend(fromusername, fromnickname, keyword)

        if self.accept_friend_config.get("keywords_group_invitation", False):
            await self.send_message.send_welcome_message(self.client, fromusername, "🤖 已经邀请你进入群。")
            return ("group_invite", True, {"keyword": keyword, "wxid": fromusername, "nickname": fromnickname})

        await self.send_message.send_welcome_message(self.client, fromusername, None)
        return ("group_invite", False, {"keyword": keyword, "wxid": fromusername, "nickname": fromnickname})

    async def rename_friend(self, fromusername: str, fromnickname: str, keyword: str) -> None:
        """
        重命名好友备注。

        :param fromusername: 申请者用户名
        :param fromnickname: 申请者昵称
        :param keyword: 触发的关键词
        """
        await asyncio.sleep(2)
        new_remark = f"{fromnickname}_{keyword}"
        await self.client.set_friend_remark(fromusername, new_remark)
        logger.info(f"Renamed friend: {fromnickname} -> {new_remark}")