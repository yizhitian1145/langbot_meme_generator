from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from pkg.platform.types import MessageChain, Image, Plain
import asyncio
import json
import httpx
import os

@register(name="MemeGenerator", description="生成表情包", version="0.1", author="Bard")
class MemeGeneratorPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        self.host = host  # 保留 self.host 以备将来使用
        self.meme_api = "http://127.0.0.1:2233"

    async def initialize(self):
        try:
            import meme_generator
        except ImportError:
            self.ap.logger.error("未安装 meme_generator，请先安装：pip install meme_generator")  # 使用 self.ap.logger
            return False

        resource_dir = os.path.expanduser("~/.config/meme_generator/resources")
        if not os.path.exists(resource_dir):
            self.ap.logger.warning("meme_generator 资源文件未下载，请手动下载或运行 `meme download` 命令下载")  # 使用 self.ap.logger

        return True


    @handler(PersonNormalMessageReceived)
    async def person_normal_message_received(self, ctx: EventContext):
        msg = ctx.event.text_message
        if msg.startswith("生成表情包"):
            try:
                parts = msg.split(" ", 2)
                meme_name = parts[1]
                texts = parts[2].split(",")

                url = self.meme_api + "/memes/" + meme_name + "/"
                data = {"texts": texts}

                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(url, data=data, timeout=30)
                        resp.raise_for_status()
                        image_url = resp.url

                    if image_url:
                        ctx.add_return("reply", MessageChain([Image(url=str(image_url))]))
                        ctx.prevent_default()
                    else:
                        self.ap.logger.error("生成表情包失败，URL 为空") # 使用 self.ap.logger 记录错误
                        ctx.add_return("reply", "生成表情包失败，请检查参数或网络连接。")
                        ctx.prevent_default()

                except httpx.HTTPError as e:
                    self.ap.logger.error(f"生成表情包失败: {e}")  # 使用 self.ap.logger
                    ctx.add_return("reply", f"生成表情包失败: {e}")
                    ctx.prevent_default()
                except httpx.TimeoutException:
                    self.ap.logger.error(f"生成表情包超时")  # 使用 self.ap.logger
                    ctx.add_return("reply", f"生成表情包超时")
                    ctx.prevent_default()


            except Exception as e:
                self.ap.logger.error(f"处理消息时出错: {e}")  # 使用 self.ap.logger
                ctx.add_return("reply", f"生成表情包失败: {e}")
                ctx.prevent_default()
