"""Task 2：比较 AES-ECB 和 AES-GCM 对原始 RGB 像素的加密。"""

import argparse
import os
from pathlib import Path

from PIL import Image, ImageDraw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


OUTPUT = Path(__file__).resolve().parent / "task2_output"


def create_example_image():
    # 使用大块纯色和重复图案，使 ECB 泄露的轮廓容易观察。
    image = Image.new("RGB", (512, 384), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 288, 511, 383), fill="#246b45")
    draw.rectangle((144, 144, 368, 288), fill="#2364aa")
    draw.polygon([(112, 144), (256, 32), (400, 144)], fill="#ba3030")
    for x in (176, 288):
        draw.rectangle((x, 176, x + 48, 224), fill="#ffcf40")
    draw.rectangle((232, 240, 280, 288), fill="#493627")
    return image


def encrypt_ecb(data, key):
    # PKCS7 填充已经准备好：AES 的块长是 128 位，即 16 字节。
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return enc.update(padded_data) + enc.finalize()


def decrypt_ecb(ciphertext, key):
    dec = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    padded = dec.update(ciphertext) + dec.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def encrypt_gcm(data, key, nonce):
    return AESGCM(key).encrypt(nonce, data, None)


def decrypt_gcm(ciphertext, key, nonce):
    return AESGCM(key).decrypt(nonce, ciphertext, None)


def save_comparison(original, ecb_image, gcm_image):
    width, height = original.size
    comparison = Image.new("RGB", (width * 3, height + 40), "white")
    draw = ImageDraw.Draw(comparison)
    for index, (label, image) in enumerate([
        ("Original", original), ("AES-ECB", ecb_image), ("AES-GCM", gcm_image)
    ]):
        draw.text((index * width + 16, 12), label, fill="black")
        comparison.paste(image, (index * width, 40))
    comparison.save(OUTPUT / "comparison.png")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--image", type=Path, help="使用自己的图片，默认生成房屋图案")
parser.add_argument("--run", action="store_true", help="运行加密实验")
args = parser.parse_args()

OUTPUT.mkdir(exist_ok=True)
if args.image:
    with Image.open(args.image) as source:
        original = source.convert("RGB")
else:
    original = create_example_image()
original.save(OUTPUT / "original.png")
data = original.tobytes()
print("原图：", OUTPUT / "original.png")
print(f"图片尺寸：{original.size}；原始 RGB 像素：{len(data)} 字节")

if args.run:
    # 每次运行生成一个新的 AES-256 key；本次实验的两个模式共用此 key。
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ecb_ciphertext = encrypt_ecb(data, key)
    gcm_ciphertext = encrypt_gcm(data, key, nonce)

    # 只有可视化副本被截取为图片长度，完整密文保留用于解密。
    # GCM 返回值末尾含 16 字节认证标签；标签不属于可显示的像素。
    ecb_image = Image.frombytes("RGB", original.size, ecb_ciphertext[:len(data)])
    gcm_image = Image.frombytes("RGB", original.size, gcm_ciphertext[:len(data)])
    ecb_image.save(OUTPUT / "ecb.png")
    gcm_image.save(OUTPUT / "gcm.png")
    save_comparison(original, ecb_image, gcm_image)

    ecb_plaintext = decrypt_ecb(ecb_ciphertext, key)
    gcm_plaintext = decrypt_gcm(gcm_ciphertext, key, nonce)
    if ecb_plaintext != data or gcm_plaintext != data:
        raise RuntimeError("解密结果与原始像素不一致，请检查实现")
    print("ECB 和 GCM 均成功还原原始像素")

    tampered = bytearray(gcm_ciphertext)
    tampered[0] ^= 1
    try:
        decrypt_gcm(bytes(tampered), key, nonce)
    except InvalidTag:
        print("GCM 成功拒绝被篡改的密文")
    else:
        raise RuntimeError("篡改检测未通过，请检查 GCM 解密实现")
    print("对比图：", OUTPUT / "comparison.png")
else:
    print("原图已生成；添加 --run 运行实验。")
