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
        self.host = host
        self.meme_api = "http://127.0.0.1:2233"

    async def initialize(self):
        try:
            import meme_generator
        except ImportError:
            self.ap.logger.error("未安装 meme_generator，请先安装：pip install meme_generator")
            return False

        resource_dir = os.path.expanduser("~/.config/meme_generator/resources")
        if not os.path.exists(resource_dir):
            try:
                from meme_generator.download import download_resource
                self.ap.logger.info("正在下载 meme_generator 资源文件...")
                await asyncio.to_thread(download_resource)
                self.ap.logger.info("meme_generator 资源文件下载完成。")
            except Exception as e:
                self.ap.logger.error(f"下载 meme_generator 资源文件失败: {e}")
                return False

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
                        self.ap.logger.error("生成表情包失败，URL 为空")
                        ctx.add_return("reply", "生成表情包失败，请检查参数或网络连接。")
                        ctx.prevent_default()

                except httpx.HTTPError as e:
                    self.ap.logger.error(f"生成表情包失败: {e}")
                    ctx.add_return("reply", f"生成表情包失败: {e}")
                    ctx.prevent_default()
                except httpx.TimeoutException:
                    self.ap.logger.error(f"生成表情包超时")
                    ctx.add_return("reply", f"生成表情包超时")
                    ctx.prevent_default()


            except Exception as e:
                self.ap.logger.error(f"处理消息时出错: {e}")
                ctx.add_return("reply", f"生成表情包失败: {e}")
                ctx.prevent_default()
