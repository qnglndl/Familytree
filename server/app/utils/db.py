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

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.port = int(os.getenv('DB_PORT'))
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"数据库连接错误: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query, params=None):
        """执行查询"""
        try:
            if not self._check_connection():
                self.disconnect()
                self.connect()
            self.cursor.execute(query, params)
            self.conn.commit()
            # 关键：主分支也保存 lastrowid
            self.lastrowid = self.cursor.lastrowid
            return True
        except Exception as e:
            print(f"查询执行错误: {e}")
            if self.conn:
                self.conn.rollback()
            # 重试分支已经加了 lastrowid，这里保持不变
            try:
                self.disconnect()
                self.connect()
                self.cursor.execute(query, params)
                self.conn.commit()
                self.lastrowid = self.cursor.lastrowid
                return True
            except Exception as retry_error:
                print(f"重试查询执行错误: {retry_error}")
                if self.conn:
                    self.conn.rollback()
                return False
    
    def fetch_all(self, query, params=None):
        """获取所有结果"""
        try:
            # 检查连接是否有效，如有必要则重新连接
            if not self._check_connection():
                self.disconnect()
                self.connect()
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取全部错误: {e}")
            # 如果出现连接错误，尝试重新连接并重试执行
            try:
                self.disconnect()
                self.connect()
                self.cursor.execute(query, params)
                return self.cursor.fetchall()
            except Exception as retry_error:
                print(f"重试获取全部错误: {retry_error}")
                return []
    
    def _check_connection(self):
        """检查连接是否仍然有效"""
        if not self.conn:
            return False
        try:
            # 使用更可靠的方式检查连接
            # 不使用 ping()，而是使用在不同 MySQL 版本中都能工作的简单查询
            self.cursor.execute("SELECT 1")
            self.cursor.fetchone()
            return True
        except:
            return False
    
    def fetch_one(self, query, params=None):
        """获取单条结果"""
        try:
            # 检查连接是否有效，如有必要则重新连接
            if not self._check_connection():
                self.disconnect()
                self.connect()
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"获取单条记录错误: {e}")
            # 如果出现连接错误，尝试重新连接并重试执行
            try:
                self.disconnect()
                self.connect()
                self.cursor.execute(query, params)
                return self.cursor.fetchone()
            except Exception as retry_error:
                print(f"重试获取单条记录错误: {retry_error}")
                return None
    
    def fetch_scalar(self, query, params=None):
        """获取标量值"""
        try:
            # 检查连接是否有效，如有必要则重新连接
            if not self._check_connection():
                self.disconnect()
                self.connect()
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            if result:
                return list(result.values())[0]
            return None
        except Exception as e:
            print(f"获取标量值错误: {e}")
            # 如果出现连接错误，尝试重新连接并重试执行
            try:
                self.disconnect()
                self.connect()
                self.cursor.execute(query, params)
                result = self.cursor.fetchone()
                if result:
                    return list(result.values())[0]
                return None
            except Exception as retry_error:
                print(f"重试获取标量值错误: {retry_error}")
                return None

# 创建数据库实例
db = Database()
