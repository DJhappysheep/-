"""
图片处理工具
压缩图片 + 二进制转 base64
"""
import io
import base64
from PIL import Image


def compress_image(image_bytes: bytes, max_size: int = 1280, quality: int = 85) -> bytes:
    """
    压缩图片：长边缩到 max_size，转 JPEG

    image_bytes: 原图二进制
    max_size: 长边最大像素（默认 1280）
    quality: JPEG 质量 1-100（默认 85）
    返回: 压缩后的 JPEG 二进制
    """
    img = Image.open(io.BytesIO(image_bytes))

    # 长边超过 max_size 才缩
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))

    # 如果有透明通道（PNG），转成白底 RGB
    if img.mode in ('RGBA', 'P'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.convert('RGBA') if img.mode == 'P' else img)
        img = bg
    else:
        img = img.convert('RGB')

    # 转 JPEG 压缩
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    return buf.getvalue()


def image_to_base64(image_bytes: bytes) -> str:
    """
    图片二进制转 base64 字符串（调 API 要用）
    """
    return base64.b64encode(image_bytes).decode()
