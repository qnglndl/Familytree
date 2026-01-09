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
检查数据库表结构脚本
用于查看family_tree数据库中的表结构，特别是user_tab表
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库连接参数
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'db': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}

print("=== 数据库表结构检查 ===")

try:
    # 连接数据库
    conn = pymysql.connect(**db_config)
    print("✅ 数据库连接成功!")
    
    # 获取数据库中的所有表
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"\n📊 数据库中共有 {len(tables)} 个表:")
        for idx, table in enumerate(tables, 1):
            table_name = table[0]
            print(f"   {idx}. {table_name}")
    
    # 检查user_tab表是否存在
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE 'user_tab'")
        user_table = cursor.fetchone()
        
        if user_table:
            print("\n✅ user_tab表存在")
            # 查看user_tab表的结构
            cursor.execute("DESCRIBE user_tab")
            structure = cursor.fetchall()
            
            print("\n📋 user_tab表结构:")
            for field in structure:
                print(f"   {field[0]:<15} {field[1]:<20} {field[2]:<8} {field[3]:<8} {field[4]:<8} {field[5]:<8}")
            
            # 查看user_tab表中的数据
            cursor.execute("SELECT id, account, name FROM user_tab LIMIT 5")
            users = cursor.fetchall()
            
            print(f"\n👥 user_tab表中有 {len(users)} 条记录:")
            for user in users:
                print(f"   ID: {user[0]}, 账号: {user[1]}, 姓名: {user[2]}")
        else:
            print("\n❌ user_tab表不存在")
            # 查看所有表的详细信息
            print("\n📋 所有表的详细信息:")
            with conn.cursor() as cursor:
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"DESCRIBE {table_name}")
                    structure = cursor.fetchall()
                    print(f"\n   表名: {table_name}")
                    for field in structure:
                        print(f"      {field[0]:<15} {field[1]:<20} {field[2]:<8}")
    
    # 关闭连接
    conn.close()
    print("\n🔚 连接已关闭")
    
except Exception as e:
    print(f"❌ 发生错误: {e}")

finally:
    print("\n=== 检查完成 ===")
