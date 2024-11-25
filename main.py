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
        self.meme_api = "http://127.0.0.1:2233"


    async def initialize(self):
        # 检查 meme-generator 是否已安装
        try:
            import meme_generator
        except ImportError:
            self.host.logger.error("未安装 meme_generator，请先安装：pip install meme_generator")
            return False

        # 检查 meme-generator 的资源文件是否已下载
        resource_dir = os.path.expanduser("~/.config/meme_generator/resources")
        if not os.path.exists(resource_dir):
            self.host.logger.warning("meme_generator 资源文件未下载，请手动下载或运行 `meme download` 命令下载")


        # 启动 meme-generator 的 API 服务 (如果需要)
        #  这里假设用户已经自行启动了 meme-generator 的 API 服务，
        #  插件不负责启动服务，避免端口冲突等问题。
        #  如果需要插件自动启动服务，需要更复杂的逻辑处理。


        return True

    @llm_func(name="generate_meme")
    async def generate_meme(self, meme_name: str, texts: list, args: dict = None):
        """
        生成表情包

        Args:
            meme_name (str): 表情包名称
            texts (list): 表情包文字
            args (dict, optional):  其他参数. Defaults to None.

        Returns:
            str: 生成的表情包图片链接
        """

        url = self.meme_api + meme_name + "/"

        data = {"texts": texts}
        if args:
            data["args"] = json.dumps(args)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=data)
                resp.raise_for_status() # 抛出异常如果请求失败

            return resp.url # 返回图片链接

        except httpx.HTTPError as e:
            self.host.logger.error(f"生成表情包失败: {e}")
            return f"生成表情包失败: {e}"


    @handler(PersonNormalMessageReceived)
    async def person_normal_message_received(self, ctx: EventContext):
        # 示例：根据用户消息生成表情包
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

