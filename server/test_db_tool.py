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

# -*- coding: utf-8 -*-
"""
测试数据库工具类脚本
模拟后端实际使用数据库工具类的方式
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.db import db

print("=== 数据库工具类测试 ===")

# 测试1: 初始化检查
print("\n1. 初始化检查:")
print(f"   db对象类型: {type(db)}")
print(f"   初始连接状态: {db.conn is not None}")

# 测试2: 执行fetch_one方法
print("\n2. 测试fetch_one方法:")
try:
    # 尝试执行登录相关的查询
    user = db.fetch_one(
        "SELECT id, name, phone, account, password FROM user_tab WHERE account = %s",
        ('test',)
    )
    
    if user:
        print("✅ 查询成功，获取到用户数据:")
        print(f"   ID: {user['id']}, 账号: {user['account']}, 姓名: {user['name']}")
    else:
        print("⚠️ 查询执行成功，但未找到用户")
        
except Exception as e:
    print(f"❌ 查询出错: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 测试连接状态
print("\n3. 连接状态检查:")
print(f"   连接对象: {db.conn}")
print(f"   游标对象: {db.cursor}")

# 测试4: 测试多次查询
print("\n4. 测试多次查询:")
try:
    for i in range(3):
        user = db.fetch_one(
            "SELECT id, account FROM user_tab WHERE account = %s",
            ('test',)
        )
        print(f"   查询 {i+1}: {'成功' if user else '未找到'}")
        
except Exception as e:
    print(f"❌ 多次查询出错: {e}")

# 测试5: 测试异常处理
print("\n5. 测试异常处理:")
try:
    # 执行一个错误的SQL查询
    result = db.fetch_one("SELECT * FROM non_existent_table")
    print(f"   结果: {result}")
except Exception as e:
    print(f"❌ 异常捕获: {e}")

# 测试6: 测试族人详情查询
print("\n6. 测试族人详情查询:")
try:
    person = db.fetch_one(
        "SELECT * FROM family_user_tab WHERE id = %s AND (is_delete = 0 OR is_delete is null)",
        (1211,)
    )
    
    if person:
        print(f"✅ 成功获取族人数据: ID = {person['id']}, 姓名 = {person['name']}")
    else:
        print("⚠️ 未找到该族人")
        
except Exception as e:
    print(f"❌ 查询出错: {e}")

print("\n=== 测试完成 ===")
