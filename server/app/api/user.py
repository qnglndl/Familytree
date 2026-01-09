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
用户管理API模块

该模块处理家庭树应用的用户管理相关接口，包括用户列表查询、编辑、禁用/启用、重置密码和新增用户功能。

依赖模块：
- Flask: Web框架，用于创建API接口
- Response: 自定义响应类，统一API返回格式
- db: 数据库操作工具，用于数据库交互
- password_manager: 密码管理工具，用于密码哈希和验证
- uuid: 用于生成唯一ID
- random: 用于生成随机密码
"""

from flask import Blueprint, request, jsonify
from app import Response
from app.utils.db import db
from app.utils.password import password_manager
import uuid
import random
import string
from datetime import datetime

# 创建Flask蓝图，定义用户管理相关的API路由
bp = Blueprint('user', __name__)

@bp.route('/list', methods=['POST'])
def get_user_list():
    """
    获取用户列表接口
    
    请求方式: POST
    请求URL: /user/list
    
    请求参数 (JSON):
        - search_text: str, 可选, 搜索文本，用于模糊查询用户姓名、账号和手机
        - page: int, 必填, 当前页码
        - page_size: int, 必填, 每页条数
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: dict, 响应数据
            - list: list, 用户列表
                - id: str, 用户ID
                - account: str, 账号
                - name: str, 用户名
                - phone: str, 手机号码
                - created_at: str, 注册时间
                - last_login_time: str, 最近登录时间
                - status: str, 状态 (0: 启用, 1: 禁用)
            - total: int, 总记录数
    
    状态码说明:
        - 200: 查询成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
    """
    data = request.get_json()
    if not data:
        return Response.error(400, "请求参数不能为空")
    
    page = data.get('page', 1)
    page_size = data.get('page_size', 20)
    search_text = data.get('search_text', '')
    
    # 构建查询条件
    where_clause = ""
    params = []
    
    if search_text:
        where_clause = "WHERE name LIKE %s OR account LIKE %s OR phone LIKE %s"
        params = [f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"]
    
    # 计算分页偏移量
    offset = (page - 1) * page_size
    
    # 查询用户列表
    query = f"""
    SELECT id, account, name, phone, created_at, last_login_time, status 
    FROM user_tab 
    {where_clause} 
    ORDER BY created_at DESC 
    LIMIT %s OFFSET %s
    """
    
    params.extend([page_size, offset])
    users = db.fetch_all(query, tuple(params))
    for user in users:
        if user['created_at']:
            user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if user['last_login_time']:
            user['last_login_time'] = user['last_login_time'].strftime('%Y-%m-%d %H:%M:%S')
    
    # 查询总记录数
    count_query = f"SELECT COUNT(*) as total FROM user_tab {where_clause}"
    count_result = db.fetch_one(count_query, tuple(params[:-2]))
    total = count_result['total'] if count_result else 0
    
    return Response.success(
        {
            "list": users,
            "total": total
        },
        "查询成功"
    )

@bp.route('/edit', methods=['POST'])
def edit_user():
    """
    编辑用户信息接口
    
    请求方式: POST
    请求URL: /user/edit
    
    请求参数 (JSON):
        - id: str, 必填, 用户ID
        - name: str, 必填, 用户名
        - phone: str, 必填, 手机号码
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
    
    状态码说明:
        - 200: 编辑成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
        - 1001: 用户不存在
        - 1002: 手机号码已存在
    """
    data = request.get_json()
    if not data:
        return Response.error(400, "请求参数不能为空")
    
    required_fields = ['id', 'name', 'phone']
    for field in required_fields:
        if not data.get(field):
            return Response.error(400, f"{field}不能为空")
    
    user_id = data['id']
    name = data['name']
    phone = data['phone']
    
    # 检查用户是否存在
    existing_user = db.fetch_one(
        "SELECT id FROM user_tab WHERE id = %s",
        (user_id,)
    )
    if not existing_user:
        return Response.error(1001, "用户不存在")
    
    # 检查手机号码是否已存在（排除当前用户）
    existing_phone = db.fetch_one(
        "SELECT id FROM user_tab WHERE phone = %s AND id != %s",
        (phone, user_id)
    )
    if existing_phone:
        return Response.error(1002, "手机号码已存在")
    
    # 更新用户信息
    query = """
    UPDATE user_tab 
    SET name = %s, phone = %s 
    WHERE id = %s
    """
    params = (name, phone, user_id)
    
    if not db.execute_query(query, params):
        return Response.error(500, "编辑失败")
    
    return Response.success({}, "编辑成功")

@bp.route('/toggle_status', methods=['POST'])
def toggle_user_status():
    """
    切换用户状态接口
    
    请求方式: POST
    请求URL: /user/toggle_status
    
    请求参数 (JSON):
        - id: str, 必填, 用户ID
        - status: str, 必填, 要切换的状态 (1: 禁用, 0: 启用)
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
    
    状态码说明:
        - 200: 状态更新成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
        - 1001: 用户不存在
    """
    data = request.get_json()
    if not data:
        return Response.error(400, "请求参数不能为空")
    
    required_fields = ['id', 'status']
    for field in required_fields:
        if not data.get(field):
            return Response.error(400, f"{field}不能为空")
    
    user_id = data['id']
    status = data['status']
    
    # 检查用户是否存在
    existing_user = db.fetch_one(
        "SELECT id FROM user_tab WHERE id = %s",
        (user_id,)
    )
    if not existing_user:
        return Response.error(1001, "用户不存在")
    
    # 更新用户状态
    query = """
    UPDATE user_tab 
    SET status = %s 
    WHERE id = %s
    """
    params = (status, user_id)
    
    if not db.execute_query(query, params):
        return Response.error(500, "状态更新失败")
    
    return Response.success({}, "状态更新成功")

@bp.route('/reset_password', methods=['POST'])
def reset_user_password():
    """
    重置用户密码接口
    
    请求方式: POST
    请求URL: /user/reset_password
    
    请求参数 (JSON):
        - id: str, 必填, 用户ID
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: dict, 响应数据
            - new_password: str, 生成的新密码
    
    状态码说明:
        - 200: 密码重置成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
        - 1001: 用户不存在
    """
    data = request.get_json()
    if not data:
        return Response.error(400, "请求参数不能为空")
    
    required_fields = ['id']
    for field in required_fields:
        if not data.get(field):
            return Response.error(400, f"{field}不能为空")
    
    user_id = data['id']
    
    # 检查用户是否存在
    existing_user = db.fetch_one(
        "SELECT id FROM user_tab WHERE id = %s",
        (user_id,)
    )
    if not existing_user:
        return Response.error(1001, "用户不存在")
    
    # 生成随机密码（8位，包含大小写字母和数字）
    characters = string.ascii_letters + string.digits
    new_password = ''.join(random.choice(characters) for _ in range(8))
    
    # 哈希新密码
    hashed_password = password_manager.hash_password(new_password)
    
    # 更新密码
    query = """
    UPDATE user_tab 
    SET password = %s 
    WHERE id = %s
    """
    params = (hashed_password, user_id)
    
    if not db.execute_query(query, params):
        return Response.error(500, "密码重置失败")
    
    return Response.success({
        "new_password": new_password
    }, "密码重置成功")

@bp.route('/add', methods=['POST'])
def add_user():
    """
    新增用户接口
    
    请求方式: POST
    请求URL: /user/add
    
    请求参数 (JSON):
        - account: str, 必填, 账号
        - password: str, 必填, 密码
        - name: str, 必填, 用户名
        - phone: str, 必填, 手机号码
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
    
    状态码说明:
        - 200: 新增成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
        - 1001: 账号已存在
        - 1002: 手机号码已存在
    """
    data = request.get_json()
    if not data:
        return Response.error(400, "请求参数不能为空")
    
    required_fields = ['account', 'password', 'name', 'phone']
    for field in required_fields:
        if not data.get(field):
            return Response.error(400, f"{field}不能为空")
    
    account = data['account']
    password = data['password']
    name = data['name']
    phone = data['phone']
    
    # Check if account already exists
    existing_account = db.fetch_one(
        "SELECT id FROM user_tab WHERE account = %s",
        (account,)
    )
    if existing_account:
        return Response.error(1001, "账号已存在")
    
    # Check if phone already exists
    existing_phone = db.fetch_one(
        "SELECT id FROM user_tab WHERE phone = %s",
        (phone,)
    )
    if existing_phone:
        return Response.error(1002, "手机号码已存在")
    
    # Generate user ID
    user_id = str(uuid.uuid4())[:16]
    
    # Hash password
    hashed_password = password_manager.hash_password(password)
    
    # Insert user into database
    query = """
    INSERT INTO user_tab (id, account, password, name, phone, status) 
    VALUES (%s, %s, %s, %s, %s, '0')
    """
    params = (user_id, account, hashed_password, name, phone)
    
    if not db.execute_query(query, params):
        return Response.error(500, "新增失败")
    
    return Response.success({}, "新增成功")
