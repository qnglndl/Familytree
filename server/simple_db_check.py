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
简单数据库表检查脚本
用于检查user_tab表是否存在以及基本信息
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

print("=== 简单数据库表检查 ===")

try:
    # 连接数据库
    conn = pymysql.connect(**db_config)
    print("✅ 数据库连接成功!")
    
    with conn.cursor() as cursor:
        # 1. 检查user_tab表是否存在
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s", 
                      (os.getenv('DB_NAME'), 'user_tab'))
        table_exists = cursor.fetchone()[0] == 1
        
        if table_exists:
            print("✅ user_tab表存在")
            
            # 2. 检查表中的字段
            cursor.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema = %s AND table_name = %s", 
                          (os.getenv('DB_NAME'), 'user_tab'))
            columns = cursor.fetchall()
            print(f"📋 user_tab表包含 {len(columns)} 个字段:")
            for col in columns:
                print(f"   - {col[0]}")
            
            # 3. 检查数据行数
            cursor.execute("SELECT COUNT(*) FROM user_tab")
            row_count = cursor.fetchone()[0]
            print(f"👥 user_tab表中有 {row_count} 条记录")
            
            # 4. 尝试执行登录相关的查询
            print("\n🔍 尝试执行登录相关查询...")
            try:
                cursor.execute("SELECT id, name, phone, account, password FROM user_tab LIMIT 1")
                user_sample = cursor.fetchone()
                if user_sample:
                    print("✅ 查询成功，获取到用户样本数据")
                    print(f"   样本用户ID: {user_sample[0]}, 账号: {user_sample[3]}")
                else:
                    print("⚠️  查询成功，但表中没有数据")
            except Exception as e:
                print(f"❌ 查询出错: {e}")
        else:
            print("❌ user_tab表不存在")
            
            # 查看所有表名
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("\n📊 数据库中存在的表:")
            for table in tables:
                print(f"   - {table[0]}")
    
    # 关闭连接
    conn.close()
    print("\n🔚 连接已关闭")
    
except Exception as e:
    print(f"❌ 发生错误: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n=== 检查完成 ===")
