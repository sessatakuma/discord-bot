import asyncio
import io

import aiohttp
import discord
from discord import Interaction, app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageDraw import ImageDraw as ImageDrawType

from config.settings import API_URL
from core.bot_core import KumaBot


async def mark_text_handler(
    interaction: Interaction, text: str, session: aiohttp.ClientSession
) -> None:
    await mark(interaction, text, session)


async def get_furigana_via_api(
    sentence: str, session: aiohttp.ClientSession
) -> list[tuple[str, str, list[int]]]:
    url = f"{API_URL}/api/MarkAccent/"
    try:
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
                                    result.append(
                                        (
                                            sw_surface,
                                            sw_furi,
                                            accent[: len(sw_furi)],
                                        )
                                    )
                                    accent = accent[len(sw_furi) :]
                                else:
                                    result.append(
                                        (
                                            sw_surface,
                                            sw_surface,
                                            accent[: len(sw_surface)],
                                        )
                                    )
                                    accent = accent[len(sw_surface) :]
                        else:
                            result.append((surface, furigana, accent))
                    return result
    except Exception as e:
        print("API error:", e)
    return []


# accent rendering
def draw_accent(
    d: ImageDrawType,
    x: int,
    y: int,
    width: int,
    furi_height: int,
    accent_type: int,
    n_kanji: int,
    n_furi: int,
    idx: int,
    furi_yes: int,
) -> None:
    """
    d: ImageDraw object
    x, y: 左上角位置
    width: 該文字區域寬度
    furi_height: 振假名高度 (用來估算線的垂直位置)
    accent_type: 0,1,2
    """
    line_y = y - 30  # furi高度

    # 沒furi 畫線寬度漢字寬
    if furi_yes == 0:
        if accent_type == 1:
            d.line(
                (x + idx * width, line_y, x + (idx + 1) * width, line_y),
                fill=(255, 0, 0),
                width=2,
            )
        elif accent_type == 2:
            d.line(
                (x + idx * width, line_y, x + (idx + 1) * width, line_y),
                fill=(255, 0, 0),
                width=2,
            )
            d.line(
                (
                    x + (idx + 1) * width,
                    line_y,
                    x + (idx + 1) * width,
                    line_y + furi_height,
                ),
                fill=(255, 0, 0),
                width=2,
            )
        else:
            pass

    # 有furi 畫線寬度furi寬
    else:
        n_start = (n_kanji / 2 - n_furi / 4) * width
        if accent_type == 1:
            d.line(
                (
                    x + n_start + idx * width / 2,
                    line_y,
                    x + n_start + (idx + 1) * width / 2,
                    line_y,
                ),
                fill=(255, 0, 0),
                width=2,
            )
            if idx == 0:
                d.line((x, line_y, x + n_start, line_y), fill=(255, 0, 0), width=2)
            elif idx == n_furi - 1:
                d.line(
                    (
                        x + n_start + (idx + 1) * width / 2,
                        line_y,
                        x + n_kanji * width,
                        line_y,
                    ),
                    fill=(255, 0, 0),
                    width=2,
                )
        elif accent_type == 2:
            d.line(
                (
                    x + n_start + idx * width / 2,
                    line_y,
                    x + n_start + (idx + 1) * width / 2,
                    line_y,
                ),
                fill=(255, 0, 0),
                width=2,
            )
            d.line(
                (
                    x + n_start + (idx + 1) * width / 2,
                    line_y,
                    x + n_start + (idx + 1) * width / 2,
                    line_y + furi_height,
                ),
                fill=(255, 0, 0),
                width=2,
            )
            if idx == 0:
                d.line((x, line_y, x + n_start, line_y), fill=(255, 0, 0), width=2)
        else:
            pass


def is_kanji(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def _generate_image(
    query: list[tuple[str, str, list[int]]], draw_box: bool = False
) -> io.BytesIO:
    """Synchronous image generation function, should be executed in the thread pool"""
    base_font_size = 40
    furi_font_size = 20
    max_word_per_line = 40
    spacing = 40
    boarder_size = 20
    furi_ratio = 0.5
    font = ImageFont.truetype("./font/NotoSerifJP-Regular.otf", base_font_size)
    furi_font = ImageFont.truetype("./font/NotoSerifJP-Regular.otf", furi_font_size)

    tmp_img = Image.new(mode="RGB", size=(100, 100), color=(255, 255, 255))
    tmp_draw = ImageDraw.Draw(tmp_img)

    # 自動換行
    lines: list[list[tuple[str, str, list[int]]]] = []
    current_line: list[tuple[str, str, list[int]]] = []
    char_cnt: int = 0
    for surface, furigana, accent in query:
        if char_cnt + len(surface) > max_word_per_line:
            lines.append(current_line)
            current_line = []
            char_cnt = 0
        current_line.append((surface, furigana, accent))
        char_cnt += len(surface)
    if current_line:
        lines.append(current_line)

    query_with_newlines = "\n".join(
        "".join(surface for surface, _, _ in line) for line in lines
    )
    lines_num = len(lines)
    word_per_line = max(
        (sum(len(surface) for surface, _, _ in line) for line in lines), default=1
    )

    bbox = tmp_draw.multiline_textbbox(
        (0, 0), query_with_newlines, font=font, spacing=spacing, align="left"
    )
    furi_height = int(spacing * furi_ratio)
    empty_space = spacing - furi_height
    width = bbox[2] - bbox[0] + 2 * boarder_size
    height = bbox[3] - bbox[1] + spacing + 2 * boarder_size - empty_space
    height += furi_height + 20

    furi_width = (width - 2 * boarder_size) / word_per_line
    padding_height = (height - 2 * boarder_size + empty_space) / max(lines_num, 1)
    kanji_height = padding_height - empty_space

    img = Image.new(mode="RGBA", size=(int(width), int(height)), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    char_cnt = 0
    current_line_cnt: int = 0
    for surface, furigana, accent in query:
        if char_cnt + len(surface) > max_word_per_line:
            char_cnt = 0
            current_line_cnt += 1

        x = char_cnt * furi_width + boarder_size
        y_base = (
            boarder_size + spacing
            if lines_num == 1
            else current_line_cnt * padding_height + boarder_size + empty_space
        )

        if draw_box:
            d.rectangle(
                (x, y_base - furi_height, x + furi_width * len(surface), y_base),
                outline=(255, 0, 0),
            )
            d.rectangle(
                (x, y_base, x + furi_width * len(surface), y_base + kanji_height),
                outline=(0, 0, 255),
            )

        # 畫 furigana（只對漢字）
        if furigana and furigana != surface and any(is_kanji(c) for c in surface):
            center_x = int(x + furi_width * len(surface) / 2)
            furi_y = y_base - 5
            d.text(
                (center_x, furi_y),
                furigana,
                fill=(255, 255, 255, 255),
                font=furi_font,
                anchor="mb",
            )

        # 畫漢字/假名
        d.text(
            (x, y_base + kanji_height / 2 - 20),
            surface,
            fill=(255, 255, 255, 255),
            font=font,
            anchor="lm",
        )

        # 畫 accent
        accent_list = accent
        kanji_len = len(surface)
        furi_len = len(furigana) if furigana else kanji_len
        furi_yes = (
            1
            if furigana and furigana != surface and any(is_kanji(c) for c in surface)
            else 0
        )
        for idx, a in enumerate(accent_list):
            draw_accent(
                d,
                int(x),
                int(y_base),
                int(furi_width),
                furi_height,
                a,
                kanji_len,
                furi_len,
                idx,
                furi_yes,
            )

        char_cnt += len(surface)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


async def text2png(
    query: str, session: aiohttp.ClientSession, draw_box: bool = False
) -> tuple[bool, io.BufferedIOBase | None]:
    result = await get_furigana_via_api(query, session)
    if not result:
        print("API 讀取失敗")
        return False, None

    # Execute image generation in thread pool
    buffer = await asyncio.to_thread(_generate_image, result, draw_box)
    return True, buffer


class MarkCog(commands.Cog):
    def __init__(self, bot: KumaBot) -> None:
        self.bot = bot

    async def cog_unload(self) -> None:
        """Clean up if necessary when cog is unloaded"""
        pass

    @app_commands.command(name="mark", description="標記日文文字的假名和音調")
    @app_commands.describe(text="要查詢的文字")
    @app_commands.rename(text="文字")
    async def usage_query(self, interaction: Interaction, text: str) -> None:
        await mark(interaction, text, self.bot.session)


async def setup(bot: KumaBot) -> None:
    await bot.add_cog(MarkCog(bot))


async def mark(
    interaction: Interaction, text: str, session: aiohttp.ClientSession
) -> None:
    try:
        if len(text) < 2:
            await interaction.response.send_message("請輸入要產生圖片的文字。")
            return
        print("Generating image for:", text)
        await interaction.response.defer()
        success, buffer = await text2png(text, session, draw_box=False)
        assert success is True, "Image generation failed"
        assert buffer, "Buffer should not be None when success is True"
        await interaction.followup.send(
            file=discord.File(buffer, filename="marked_text.png")
        )
    except Exception as e:
        print(f"Error in mark function: {e}")
        await interaction.followup.send(f"發生錯誤：{e}")
