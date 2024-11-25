from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
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
        self.meme_api = "http://127.0.0.1:2233/memes/"

    async def initialize(self):
        try:
            import meme_generator
        except ImportError:
            self.host.logger.error("未安装 meme_generator，请先安装：pip install meme_generator")
            return False

        resource_dir = os.path.expanduser("~/.config/meme_generator/resources")
        if not os.path.exists(resource_dir):
            self.host.logger.warning("meme_generator 资源文件未下载，请手动下载或运行 `meme download` 命令下载")

        return True

    @llm_func(name="generate_meme")
    async def generate_meme(self, meme_name: str, texts: list, args: dict = None):
        """Generate a meme image using meme-generator.

        Args:
            meme_name (str): The name of the meme template to use.
                For example: 'petpet', 'nokia', etc.
            texts (list): List of texts to put on the meme.
                Each text will be placed in order according to the template.
            args (dict, optional): Additional arguments for meme generation.
                Specific to each meme template. Defaults to None.

        Returns:
            str: URL of the generated meme image.
        """
        url = self.meme_api + meme_name + "/"

        data = {"texts": texts}
        if args:
            data["args"] = json.dumps(args)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=data)
                resp.raise_for_status()

            return resp.url

        except httpx.HTTPError as e:
            self.host.logger.error(f"生成表情包失败: {e}")
            return f"生成表情包失败: {e}"

    @handler(PersonNormalMessageReceived)
    async def person_normal_message_received(self, ctx: EventContext):
        msg = ctx.event.text_message
        if msg.startswith("生成表情包"):
            try:
                parts = msg.split(" ", 2)
                meme_name = parts[1]
                texts = parts[2].split(",")

                image_url = await self.generate_meme(meme_name, texts)

                if image_url:
                    ctx.add_return("reply", MessageChain([Image(url=str(image_url))]))
                    ctx.prevent_default()

            except Exception as e:
                self.host.logger.error(f"处理消息时出错: {e}")
                ctx.add_return("reply", f"生成表情包失败: {e}")
                ctx.prevent_default()
