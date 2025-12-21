'''
Author: qnglndl fhfhfhfu114514@163.com
Date: 2025-12-20 05:15:03
LastEditors: qnglndl fhfhfhfu114514@163.com
LastEditTime: 2025-12-21 09:07:09
FilePath: /Familytree/server/app/utils/password.py
Description: 密码管理工具类

Copyright (c) 2025 by ${git_name_email}, All Rights Reserved. 
'''
'''
                       _oo0oo_
                      o8888888o
                      88" . "88
                      (| -_- |)
                      0\  =  /0
                    ___/`---'\___
                  .' \\|     |// '.
                 / \\|||  :  |||// \
                / _||||| -:- |||||- \
               |   | \\\  - /// |   |
               | \_|  ''\---/''  |_/ |
               \  .-\__  '-'  ___/-. /
             ___'. .'  /--.--\  `. .'___
          ."" '<  `.___\_<|>_/___.' >' "".
         | | :  `- \`.;`\ _ /`;.`/ - ` : | |
         \  \ `_.   \_ __\ /__ _/   .-` /  /
     =====`-.____`.___ \_____/___.-`___.-'=====
                       `=---='


     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

           佛祖保佑     永不宕机     永无BUG

       佛曰:  
               写字楼里写字间，写字间里程序员；  
               程序人员写程序，又拿程序换酒钱。  
               酒醒只在网上坐，酒醉还来网下眠；  
               酒醉酒醒日复日，网上网下年复年。  
               但愿老死电脑间，不愿鞠躬老板前；  
               奔驰宝马贵者趣，公交自行程序员。  
               别人笑我忒疯癫，我笑自己命太贱；  
               不见满街漂亮妹，哪个归得程序员？
'''

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os

class PasswordManager:
    def __init__(self):
        self.salt = os.urandom(16)  # 生成16字节的随机盐值
        self.backend = default_backend()  # 获取默认的加密后端
    
    def hash_password(self, password):
        """对密码进行哈希处理"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),  # 使用SHA256哈希算法
            length=32,  # 生成的密钥长度为32字节
            salt=self.salt,  # 使用类实例中的盐值
            iterations=100000,  # 迭代次数为100000
            backend=self.backend  # 使用指定的加密后端
        )
        hash_bytes = kdf.derive(password.encode())  # 对编码后的密码进行派生计算
        hash_str = base64.urlsafe_b64encode(hash_bytes).decode()  # 将哈希字节转换为URL安全的Base64字符串
        salt_str = base64.urlsafe_b64encode(self.salt).decode()  # 将盐值转换为URL安全的Base64字符串
        return f"{salt_str}${hash_str}"  # 返回盐值和哈希值拼接的字符串
    
    def verify_password(self, password, hashed_password):
        """验证密码与哈希值是否匹配"""
        if not hashed_password or '$' not in hashed_password:  # 检查哈希字符串格式是否正确
            return False
        
        salt_str, hash_str = hashed_password.split('$', 1)  # 拆分盐值和哈希值字符串
        salt = base64.urlsafe_b64decode(salt_str.encode())  # 将盐值字符串解码为字节
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,  # 使用从哈希字符串中提取的盐值
            iterations=100000,
            backend=self.backend
        )
        
        try:
            hash_bytes = base64.urlsafe_b64decode(hash_str.encode())  # 将哈希值字符串解码为字节
            kdf.verify(password.encode(), hash_bytes)  # 验证密码
            return True
        except Exception as e:
            print(f"密码验证错误: {e}")  # 打印验证错误信息
            return False

# 创建密码管理器实例
password_manager = PasswordManager()