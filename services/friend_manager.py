'''
Author: diudiu62
Date: 2025-03-04 18:23:22
LastEditTime: 2025-03-12 14:51:11
'''
import asyncio
import xml.etree.ElementTree as ET
from astrbot.api import logger
from .base_manager import BaseManager
from .group_manager import GroupManager


class FriendManager(BaseManager):

    async def accept_friend_request(self, event) -> tuple:
        """
        处理好友请求，检查是否包含关键词并做出相应的操作。

        :param event: event元数据
        """
        content_xml = event.message_obj.raw_message.get(
            "Content", {}).get("string", "")
        content_xml = ET.fromstring(content_xml)
        remark = content_xml.attrib.get('content')
        fromnickname = content_xml.attrib.get('fromnickname')
        fromusername = content_xml.attrib.get('fromusername')
        v3 = content_xml.attrib.get('encryptusername')
        v4 = content_xml.attrib.get('ticket')

        logger.info("好友申请备注: {}".format(remark))

        keywords = self.accept_friend_config.get("keywords", [])
        if not keywords:
            logger.warning("没有设置关键词，无法审核好友。")
            return None, None

        for keyword in keywords:
            if keyword in remark:
                result = await self.process_friend_request(v3, v4, remark, fromnickname, fromusername, keyword)
                return fromusername, result

        logger.info(f"{fromnickname} ：好友申请待审核.")
        return None, None

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
        result = ""
        try:
            logger.info(f"{fromnickname} 申请好友触发关键词： ({keyword})")
            delay = int(self.accept_friend_config.get(
                "accept_friend_delay", 0))
            await asyncio.sleep(delay)
            self.client.add_contacts(self.appid, 3, 3, v3, v4, remark)
            logger.info(f"添加好友: {fromnickname}")
            await asyncio.sleep(2)

            if self.accept_friend_config.get("rename", False):
                # 备注好友
                await self.rename_friend(fromusername, fromnickname, keyword)

            if self.accept_friend_config.get("keywords_group_invitation", False):
                #  邀请进群
                group_manager = GroupManager(
                    self.base_url, self.appid, self.gewechat_token, self.config)
                result = await group_manager.accept_friend_group_invitation(keyword, fromusername, fromnickname)
            return result
        except ExceptionGroup as e:
            return f"处理添加好友有错误：{e}"

    async def rename_friend(self, fromusername: str, fromnickname: str, keyword: str) -> None:
        """
        重命名好友备注。

        :param fromusername: 申请者用户名
        :param fromnickname: 申请者昵称
        :param keyword: 触发的关键词
        """
        await asyncio.sleep(2)
        new_remark = f"{fromnickname}_{keyword}"
        self.client.set_friend_remark(self.appid, fromusername, new_remark)
        logger.info(f"修改好友备注: {fromnickname} -> {new_remark}")

    async def search_friend(self, contactsinfo: str) -> None:
        """
        搜索好友。

        :param contactsinfo: 搜索的联系人信息，微信号、手机号...
        """
        resault = self.client.search_contacts(self.appid, contactsinfo)
        if resault['ret'] == 200:
            return True
        else:
            return False
