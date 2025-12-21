'''
Author: qnglndl fhfhfhfu114514@163.com
Date: 2025-12-20 05:15:02
LastEditors: qnglndl fhfhfhfu114514@163.com
LastEditTime: 2025-12-21 09:05:46
FilePath: /Familytree/server/app/api/home.py
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

from flask import Blueprint, request, jsonify
from app import Response
from app.utils.db import db

# Create blueprint
bp = Blueprint('home', __name__)

@bp.route('/stats', methods=['POST'])
def get_stats():
    """获取主页统计数据"""
    try:
        # Get total persons count
        total_persons = db.fetch_scalar(
            "SELECT COUNT(id) FROM family_user_tab WHERE is_delete = 0"
        ) or 0
        
        # Get total generations count
        total_generations = db.fetch_scalar(
            "SELECT COUNT(DISTINCT generation) FROM family_user_tab WHERE is_delete = 0"
        ) or 0
        
        # Get migration count
        migration_count = db.fetch_scalar(
            "SELECT COUNT(id) FROM family_user_tab WHERE area IS NOT NULL AND area != '' AND is_delete = 0"
        ) or 0
        
        # Get generation statistics for bar chart
        generation_stats = db.fetch_all("""
            SELECT generation, COUNT(id) as count
            FROM family_user_tab
            WHERE is_delete = 0
            GROUP BY generation
            ORDER BY generation
        """)
        
        # Format response data
        stats_data = {
            "total_persons": total_persons,
            "total_generations": total_generations,
            "migration_count": migration_count,
            "generation_stats": generation_stats
        }
        
        return Response.success(stats_data, "获取统计数据成功")
    except Exception as e:
        print(f"Error getting stats: {e}")
        return Response.error(500, "获取统计数据失败")
