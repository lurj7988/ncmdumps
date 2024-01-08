# -*- coding = utf-8 -*-
# @time:2023/09/07 15:00
# Author:lurj

# https://www.cnblogs.com/cyx-b/p/13443003.html
# https://www.jianshu.com/p/ec5977ef383a
import binascii
import struct
import base64
import json
import os
from Crypto.Cipher import AES
import music_tag


class NcmDump:

    def __init__(self, file_path):
        self.file_path = file_path
        self.core_key = binascii.a2b_hex("687A4852416D736F356B496E62617857")
        self.meta_key = binascii.a2b_hex("2331346C6A6B5F215C5D2630553C2728")
        self.file = open(file_path, 'rb')
        self.comment = ''

    def unpad(self, s):
        return s[0:-(s[-1] if type(s[-1]) == int else ord(s[-1]))]

    def assert_magic(self):
        header = self.file.read(8)
        self.file.seek(2, 1)
        # 字符串转十六进制
        assert binascii.b2a_hex(header) == b'4354454e4644414d'

    def read_key_data(self):
        # 4 bytes of meta length
        key_length_bytes = self.file.read(4)
        key_length = struct.unpack('<I', bytes(key_length_bytes))[0]
        key_data_bytes = self.file.read(key_length)
        key_data_array = bytearray(key_data_bytes)
        for i in range(0, len(key_data_array)):
            # 异或运算
            key_data_array[i] ^= 0x64
        return bytes(key_data_array)

    def build_key_box(self, key_data):
        cryptor = AES.new(self.core_key, AES.MODE_ECB)
        decrypt_data = cryptor.decrypt(key_data)
        # remove "neteasecloudmusic"
        decrypt_data = self.unpad(decrypt_data)[17:]
        return self.RC4KSA(decrypt_data)

    def RC4KSA(self, decrypt_data):
        key_length = len(decrypt_data)
        key_data = bytearray(decrypt_data)
        key_box = bytearray(range(256))
        c = 0
        last_byte = 0
        key_offset = 0
        for i in range(256):
            swap = key_box[i]
            c = (swap + last_byte + key_data[key_offset]) & 0xff
            key_offset += 1
            if key_offset >= key_length:
                key_offset = 0
            key_box[i] = key_box[c]
            key_box[c] = swap
            last_byte = c
        return key_box

    def read_meta_data(self):
        meta_length_bytes = self.file.read(4)
        meta_length = struct.unpack('<I', bytes(meta_length_bytes))[0]
        meta_data_bytes = self.file.read(meta_length)
        meta_data_array = bytearray(meta_data_bytes)
        for i in range(0, len(meta_data_array)):
            meta_data_array[i] ^= 0x63
        meta_data_bytes = bytes(meta_data_array)
        self.comment = meta_data_bytes.decode('utf-8')
        # remove "163 key(Don't modify):"
        meta_data_decode = base64.b64decode(meta_data_bytes[22:])
        cryptor = AES.new(self.meta_key, AES.MODE_ECB)
        # remove "music:"
        meta_data_json = self.unpad(cryptor.decrypt(
            meta_data_decode)).decode('utf-8')[6:]
        meta_data = json.loads(meta_data_json)
        return meta_data

    def read_crc32(self):
        crc32_bytes = self.file.read(4)
        crc32 = struct.unpack('<I', bytes(crc32_bytes))[0]
        return crc32

    def read_album_image_data(self):
        self.file.seek(5, 1)
        image_size_bytes = self.file.read(4)
        image_size = struct.unpack('<I', bytes(image_size_bytes))[0]
        image_data = self.file.read(image_size)
        return image_data

    def read_music_data(self, key_box):
        musicdata = bytearray()
        while True:
            # 一次读取0x8000字节
            musicdata_array = bytearray(self.file.read(0x8000))
            if not musicdata_array:
                break
            musicdata = musicdata + musicdata_array
        return self.RC4PRGA(musicdata, key_box)

    def RC4PRGA(self, musicdata, key_box):
        musicdata_length = len(musicdata)
        for i in range(1, musicdata_length+1):
            j = i & 0xff
            musicdata[i-1] ^= key_box[(key_box[j] +
                                       key_box[(key_box[j] + j) & 0xff])
                                      & 0xff]
        return musicdata

    def write_music_data(self, meta_data, music_data):
        music_name = meta_data['musicName'] + '.' + meta_data['format']
        music_path = os.path.join(os.path.split(self.file_path)[0], music_name)
        m = open(music_path, 'wb')
        m.write(music_data)
        m.close()
        return music_path

    def fix_tags(self, music_path, meta_data, album_image_data):
        tag = music_tag.load_file(music_path)
        tag['album'] = meta_data['album']
        tag['title'] = meta_data['musicName']
        artist = []
        for i in meta_data['artist']:
            artist.append(i[0])
        tag['artist'] = artist
        tag['comment'] = self.comment
        tag['artwork'] = album_image_data
        print(tag)
        tag.save()

    def dump(self):
        # 8 bytes of header "CTENFDAM"
        # skip 2 bytes
        self.assert_magic()
        # 4 bytes of key length 然后根据长度读取key
        key_data = self.read_key_data()
        key_box = self.build_key_box(key_data)
        # 4 bytes of meta length 然后根据长度读取meta
        meta_data = self.read_meta_data()
        # 4 bytes
        self.read_crc32()
        # skip 5 bytes 然后读取4字节的图片大小
        album_image_data = self.read_album_image_data()
        # 从当前位置读取到文件末尾
        music_data = self.read_music_data(key_box)
        music_path = self.write_music_data(meta_data, music_data)
        self.fix_tags(music_path, meta_data, album_image_data)


def dump(file_path):
    # 十六进制转字符串
    core_key = binascii.a2b_hex("687A4852416D736F356B496E62617857")
    print(type(core_key), core_key, str(core_key))
    meta_key = binascii.a2b_hex("2331346C6A6B5F215C5D2630553C2728")
    print(type(meta_key), meta_key, str(meta_key))
    def unpad(s): return s[0:-(s[-1] if type(s[-1]) == int else ord(s[-1]))]
    f = open(file_path, 'rb')
    header = f.read(8)
    print('header', type(header), header, str(
        header), binascii.b2a_hex(header))
    # 字符串转十六进制
    assert binascii.b2a_hex(header) == b'4354454e4644414d'
    f.seek(2, 1)
    # 4 bytes of meta length
    key_length = f.read(4)
    key_length = struct.unpack('<I', bytes(key_length))[0]
    key_data = f.read(key_length)
    key_data_array = bytearray(key_data)
    for i in range(0, len(key_data_array)):
        # 异或运算
        key_data_array[i] ^= 0x64
    key_data = bytes(key_data_array)
    cryptor = AES.new(core_key, AES.MODE_ECB)
    # remove "neteasecloudmusic"
    print(cryptor.decrypt(key_data))
    key_data = unpad(cryptor.decrypt(key_data))[17:]
    print('key_data', key_data)
    key_length = len(key_data)
    key_data = bytearray(key_data)
    key_box = bytearray(range(256))
    c = 0
    last_byte = 0
    key_offset = 0
    for i in range(256):
        swap = key_box[i]
        c = (swap + last_byte + key_data[key_offset]) & 0xff
        key_offset += 1
        if key_offset >= key_length:
            key_offset = 0
        key_box[i] = key_box[c]
        key_box[c] = swap
        last_byte = c
    meta_length = f.read(4)
    meta_length = struct.unpack('<I', bytes(meta_length))[0]
    meta_data = f.read(meta_length)
    meta_data_array = bytearray(meta_data)
    for i in range(0, len(meta_data_array)):
        meta_data_array[i] ^= 0x63
    meta_data = bytes(meta_data_array)
    comment = meta_data.decode('utf-8')
    # remove "163 key(Don't modify):"
    meta_data = base64.b64decode(meta_data[22:])
    cryptor = AES.new(meta_key, AES.MODE_ECB)
    meta_data = unpad(cryptor.decrypt(meta_data)).decode('utf-8')[6:]
    meta_data = json.loads(meta_data)
    crc32 = f.read(4)
    crc32 = struct.unpack('<I', bytes(crc32))[0]
    f.seek(5, 1)
    image_size = f.read(4)
    image_size = struct.unpack('<I', bytes(image_size))[0]
    # 这个不能自作聪明去掉，需要读取指定长度的数据，不然转换的音频会损坏
    image_data = f.read(image_size)
    print("meta_data:", meta_data)
    # file_name = f.name.split(
    #     "/")[-1].split(".ncm")[0] + '.' + meta_data['format']
    file_name = meta_data['musicName'] + '.' + meta_data['format']
    m = open(os.path.join(os.path.split(file_path)[0], file_name), 'wb')
    chunk = bytearray()
    while True:
        chunk = bytearray(f.read(0x8000))
        chunk_length = len(chunk)
        if not chunk:
            break
        for i in range(1, chunk_length+1):
            j = i & 0xff
            chunk[i-1] ^= key_box[(key_box[j] +
                                   key_box[(key_box[j] + j) & 0xff]) & 0xff]
        m.write(chunk)
    m.close()
    f.close()
    file_path = os.path.join(os.path.split(file_path)[0], file_name)
    print(file_path)
    tag = music_tag.load_file(file_path)
    tag['album'] = meta_data['album']
    tag['title'] = meta_data['musicName']
    artist = []
    for i in meta_data['artist']:
        artist.append(i[0])
    tag['artist'] = artist
    tag['comment'] = comment
    tag['artwork'] = image_data
    print(tag)
    tag.save()
    return file_name


def file_extension(path):
    return os.path.splitext(path)[1]


if __name__ == '__main__':
    # file_path = input("请输入文件所在路径(例如：E:\\ncm_music)\n")
    # list = os.listdir(file_path)  # Get all files in folder.
    # for i in range(0, len(list)):
    #     path = os.path.join(file_path, list[i])
    #     print(path)
    #     if os.path.isfile(path):
    #         if os.path.isfile(path):
    #             if file_extension(path) == ".ncm":
    #                 try:
    #                     dump(path)
    #                 except Exception as e:
    #                     print(e)
    try:
        ncm = NcmDump("E:\\CloudMusic\\VipSongsDownload\\林子祥 - 男儿当自强.ncm")
        ncm.dump()
        # dump("E:\\CloudMusic\\VipSongsDownload\\林子祥 - 男儿当自强.ncm")
    except Exception as e:
        print(e)
    f = music_tag.load_file("E:\\CloudMusic\\林子祥 - 男儿当自强2.mp3")
    print(f)
