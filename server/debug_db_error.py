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

#!/usr/bin/env python3
"""
Debug script to trace database connection errors in the Familytree backend
"""

import pymysql
import traceback
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DebugDatabase:
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.port = int(os.getenv('DB_PORT'))
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to the database with detailed logging"""
        print("\n[DEBUG] Attempting to connect to database...")
        print(f"[DEBUG] Connection params: host={self.host}, port={self.port}, user={self.user}, db={self.db_name}")
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
            print("[DEBUG] ✅ Connection established successfully")
            print(f"[DEBUG] Connection object: {self.conn}")
            return True
        except Exception as e:
            print(f"[DEBUG] ❌ Database connection error:")
            print(f"[DEBUG] Error type: {type(e).__name__}")
            print(f"[DEBUG] Error message: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return False
    
    def disconnect(self):
        """Disconnect from the database"""
        print("\n[DEBUG] Disconnecting from database...")
        if self.cursor:
            try:
                self.cursor.close()
                print("[DEBUG] Cursor closed")
            except Exception as e:
                print(f"[DEBUG] Error closing cursor: {e}")
        if self.conn:
            try:
                self.conn.close()
                print("[DEBUG] Connection closed")
            except Exception as e:
                print(f"[DEBUG] Error closing connection: {e}")
    
    def _check_connection(self):
        """Check if the connection is still valid with detailed logging"""
        print("\n[DEBUG] Checking connection health...")
        if not self.conn:
            print("[DEBUG] ❌ Connection object is None")
            return False
        
        print(f"[DEBUG] Connection status: open={self.conn.open}")
        
        try:
            # Try ping first
            print("[DEBUG] Executing conn.ping(reconnect=False)...")
            self.conn.ping(reconnect=False)
            print("[DEBUG] ✅ ping() successful")
            
            # Try a simple query
            print("[DEBUG] Executing simple test query...")
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            print(f"[DEBUG] ✅ Simple query successful, result: {result}")
            return True
        except Exception as e:
            print(f"[DEBUG] ❌ Connection health check failed:")
            print(f"[DEBUG] Error type: {type(e).__name__}")
            print(f"[DEBUG] Error message: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return False
    
    def simulate_login_query(self, account):
        """Simulate the login query from auth.py"""
        print(f"\n[DEBUG] Simulating login query for account: {account}")
        query = "SELECT id, name, phone, account, password FROM user_tab WHERE account = %s"
        params = (account,)
        
        try:
            # Check connection first
            if not self._check_connection():
                print("[DEBUG] Connection invalid, reconnecting...")
                self.disconnect()
                if not self.connect():
                    print("[DEBUG] ❌ Failed to reconnect")
                    return None
            
            print(f"[DEBUG] Executing query: {query}")
            print(f"[DEBUG] With params: {params}")
            self.cursor.execute(query, params)
            
            print("[DEBUG] Fetching one result...")
            result = self.cursor.fetchone()
            print(f"[DEBUG] Query result: {result}")
            return result
        except Exception as e:
            print(f"[DEBUG] ❌ Fetch one error:")
            print(f"[DEBUG] Error type: {type(e).__name__}")
            print(f"[DEBUG] Error message: {e}")
            print(f"[DEBUG] Full error repr: {repr(e)}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            
            # Try to reconnect and execute again
            try:
                print("[DEBUG] Retrying after reconnect...")
                self.disconnect()
                if self.connect():
                    self.cursor.execute(query, params)
                    result = self.cursor.fetchone()
                    print(f"[DEBUG] ✅ Retry successful, result: {result}")
                    return result
            except Exception as retry_error:
                print(f"[DEBUG] ❌ Retry failed:")
                print(f"[DEBUG] Error type: {type(retry_error).__name__}")
                print(f"[DEBUG] Error message: {retry_error}")
                print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            
            return None

def main():
    print("=== Familytree Database Debug Script ===")
    
    # Create debug database instance
    debug_db = DebugDatabase()
    
    # Test connection
    if debug_db.connect():
        # Test ping functionality
        print("\n=== Testing Connection Ping ===")
        debug_db._check_connection()
        
        # Test login query
        print("\n=== Testing Login Query ===")
        debug_db.simulate_login_query("test")
        
        # Test with invalid connection
        print("\n=== Testing Invalid Connection Handling ===")
        # Force close the connection
        debug_db.conn.close()
        debug_db.conn = debug_db.conn  # Keep the reference but it's closed
        # Now test the login query which should detect the closed connection
        debug_db.simulate_login_query("test")
        
        # Cleanup
        debug_db.disconnect()
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    main()
