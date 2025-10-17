import asyncio
import io

import aiohttp
import discord
from discord import Interaction, app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from config.settings import API_URL


async def mark_text_handler(interaction, text):
    await mark(interaction, text)


async def get_furigana_via_api(sentence: str):
    url = f"{API_URL}/api/MarkAccent/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"text": sentence}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data["status"] == 200 and data["result"]:
                        result = []
                        for item in data["result"]:
                            surface = item["surface"]
                            furigana = item["furigana"]
                            accent = [a["accent_marking_type"] for a in item["accent"]]

                            # check subword
                            if "subword" in item and item["subword"]:
                                for sw in item["subword"]:
                                    sw_surface = sw["surface"]
                                    sw_furi = sw["furigana"]
                                    # check if subowrd have kanji
                                    if any("\u4e00" <= c <= "\u9fff" for c in sw_surface):
                                        result.append((sw_surface, sw_furi, accent[: len(sw_furi)]))
                                        accent = accent[len(sw_furi) :]
                                    else:
                                        result.append((sw_surface, sw_surface, accent[: len(sw_surface)]))
                                        accent = accent[len(sw_surface) :]
                            else:
                                result.append((surface, furigana, accent))
                        return result
    except Exception as e:
        print("API error:", e)
    return []


# accent rendering
def draw_accent(d, x, y, width, furiHeight, accentType, N_kanji, N_furi, idx, furi_yes):
    """
    d: ImageDraw
    x, y: 左上角位置
    width: 該文字區域寬度
    furiHeight: 振假名高度 (用來估算線的垂直位置)
    accentType: 0,1,2
    """
    lineY = y - 30  # furi高度

    # 沒furi 畫線寬度漢字寬
    if furi_yes == 0:
        if accentType == 1:
            d.line((x + idx * width, lineY, x + (idx + 1) * width, lineY), fill=(255, 0, 0), width=2)
        elif accentType == 2:
            d.line((x + idx * width, lineY, x + (idx + 1) * width, lineY), fill=(255, 0, 0), width=2)
            d.line(
                (x + (idx + 1) * width, lineY, x + (idx + 1) * width, lineY + furiHeight), fill=(255, 0, 0), width=2
            )
        else:
            pass

    # 有furi 畫線寬度furi寬
    else:
        Nstart = (N_kanji / 2 - N_furi / 4) * width
        if accentType == 1:
            d.line(
                (x + Nstart + idx * width / 2, lineY, x + Nstart + (idx + 1) * width / 2, lineY),
                fill=(255, 0, 0),
                width=2,
            )
            if idx == 0:
                d.line((x, lineY, x + Nstart, lineY), fill=(255, 0, 0), width=2)
            elif idx == N_furi - 1:
                d.line(
                    (x + Nstart + (idx + 1) * width / 2, lineY, x + N_kanji * width, lineY), fill=(255, 0, 0), width=2
                )
        elif accentType == 2:
            d.line(
                (x + Nstart + idx * width / 2, lineY, x + Nstart + (idx + 1) * width / 2, lineY),
                fill=(255, 0, 0),
                width=2,
            )
            d.line(
                (x + Nstart + (idx + 1) * width / 2, lineY, x + Nstart + (idx + 1) * width / 2, lineY + furiHeight),
                fill=(255, 0, 0),
                width=2,
            )
            if idx == 0:
                d.line((x, lineY, x + Nstart, lineY), fill=(255, 0, 0), width=2)
        else:
            pass


def is_kanji(char):
    return "\u4e00" <= char <= "\u9fff"


def _generate_image(query, drawBox=False):
    """Synchronous image generation function, should be executed in the thread pool"""
    basefontSize = 40
    furifontSize = 20
    maxWordPerLine = 40
    spacing = 40
    boarderSize = 20
    furiRatio = 0.5
    font = ImageFont.truetype("./font/NotoSerifJP-Regular.otf", basefontSize)
    furifont = ImageFont.truetype("./font/NotoSerifJP-Regular.otf", furifontSize)

    tmp_img = Image.new(mode="RGB", size=(100, 100), color=(255, 255, 255))
    tmp_draw = ImageDraw.Draw(tmp_img)

    # 自動換行
    lines = []
    current_line = []
    charCnt = 0
    for surface, furigana, accent in query:
        if charCnt + len(surface) > maxWordPerLine:
            lines.append(current_line)
            current_line = []
            charCnt = 0
        current_line.append((surface, furigana, accent))
        charCnt += len(surface)
    if current_line:
        lines.append(current_line)

    query_with_newlines = "\n".join("".join(surface for surface, _, _ in line) for line in lines)
    linesNum = len(lines)
    wordPerLine = max((sum(len(surface) for surface, _, _ in line) for line in lines), default=1)

    bbox = tmp_draw.multiline_textbbox((0, 0), query_with_newlines, font=font, spacing=spacing, align="left")
    furiHeight = int(spacing * furiRatio)
    emptySpace = spacing - furiHeight
    width = bbox[2] - bbox[0] + 2 * boarderSize
    height = bbox[3] - bbox[1] + spacing + 2 * boarderSize - emptySpace
    height += furiHeight + 20

    furiWidth = (width - 2 * boarderSize) / wordPerLine
    paddingHeight = (height - 2 * boarderSize + emptySpace) / max(linesNum, 1)
    kanjiHeight = paddingHeight - emptySpace

    img = Image.new(mode="RGBA", size=(width, height), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    charCnt = 0
    current_line = 0
    for surface, furigana, accent in query:
        if charCnt + len(surface) > maxWordPerLine:
            charCnt = 0
            current_line += 1

        x = charCnt * furiWidth + boarderSize
        y_base = boarderSize + spacing if linesNum == 1 else current_line * paddingHeight + boarderSize + emptySpace

        if drawBox:
            d.rectangle((x, y_base - furiHeight, x + furiWidth * len(surface), y_base), outline=(255, 0, 0))
            d.rectangle((x, y_base, x + furiWidth * len(surface), y_base + kanjiHeight), outline=(0, 0, 255))

        # 畫 furigana（只對漢字）
        if furigana and furigana != surface and any(is_kanji(c) for c in surface):
            centerX = int(x + furiWidth * len(surface) / 2)
            furi_y = y_base - 5
            d.text((centerX, furi_y), furigana, fill=(255, 255, 255, 255), font=furifont, anchor="mb")

        # 畫漢字/假名
        d.text((x, y_base + kanjiHeight / 2 - 20), surface, fill=(255, 255, 255, 255), font=font, anchor="lm")

        # 畫 accent
        accent_list = accent
        kanji_len = len(surface)
        furi_len = len(furigana) if furigana else kanji_len
        furi_yes = 1 if furigana and furigana != surface and any(is_kanji(c) for c in surface) else 0
        for idx, a in enumerate(accent_list):
            draw_accent(d, x, y_base, furiWidth, furiHeight, a, kanji_len, furi_len, idx, furi_yes)

        charCnt += len(surface)

    buffer: io.BufferedIOBase = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


async def text2png(query, drawBox=False):
    result = await get_furigana_via_api(query)
    if not result:
        print("API 讀取失敗")
        return False, None

    # Execute image generation in thread pool
    buffer = await asyncio.to_thread(_generate_image, result, drawBox)
    return True, buffer


class MarkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_unload(self):
        """Clean up if necessary when cog is unloaded"""
        pass

    @app_commands.command(name="mark", description="標記日文文字的假名和音調")
    @app_commands.describe(text="要查詢的文字")
    @app_commands.rename(text="文字")
    async def usage_query(self, interaction: Interaction, text: str):
        await mark(interaction, text)


async def setup(bot: commands.Bot):
    await bot.add_cog(MarkCog(bot))


async def mark(interaction: Interaction, text: str):
    if len(text) < 2:
        await interaction.response.send_message("請輸入要產生圖片的文字。")
        return
    print("Generating image for:", text)
    await interaction.response.defer()
    success, buffer = await text2png(text, drawBox=False)
    if success:
        await interaction.followup.send(file=discord.File(buffer, filename="marked_text.png"))
    else:
        await interaction.followup.send("圖片生成失敗")
