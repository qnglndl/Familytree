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
家庭信息API模块

该模块处理家庭树应用的家庭信息相关接口，包括家庭列表查询、创建家庭、添加成员等功能。

依赖模块：
- Flask: Web框架，用于创建API接口
- Response: 自定义响应类，统一API返回格式
- db: 数据库操作工具，用于数据库交互
- uuid: 用于生成唯一家庭ID和关系ID
"""

from flask import Blueprint, request, jsonify
from app import Response
from app.utils.db import db
import uuid

# 创建Flask蓝图，定义家庭相关的API路由
bp = Blueprint('family', __name__)

@bp.route('/list', methods=['POST'])
def get_family_list():
    """
    获取家庭列表接口
    
    请求方式: POST
    请求URL: /family/list
    
    请求参数 (JSON):
        - page: int, 可选, 当前页码，默认1
        - page_size: int, 可选, 每页数量，默认10
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: dict, 响应数据
            - total: int, 家庭总数
            - list: list, 家庭列表
                - id: str, 家庭ID
                - name: str, 家庭名称
                - clan_head_name: str, 族长姓名
                - clan_head_id: str, 族长ID
    
    状态码说明:
        - 200: 获取成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
    """
    data = request.get_json() or {}
    
    # Pagination
    page = data.get('page', 1)
    page_size = data.get('page_size', 10)
    offset = (page - 1) * page_size
    
    # Get total count
    total = db.fetch_scalar(
        "SELECT COUNT(id) FROM family_tab"
    ) or 0
    
    # Get family list
    families = db.fetch_all("""
        SELECT id, name, clan_head_name, clan_head_id
        FROM family_tab
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """, (page_size, offset))
    
    return Response.success(
        {
            "total": total,
            "list": families
        },
        "获取家庭列表成功"
    )

@bp.route('/create', methods=['POST'])
def create_family():
    """
    创建新家庭接口
    
    请求方式: POST
    请求URL: /family/create
    
    请求参数 (JSON):
        - name: str, 必填, 家庭名称
        - clan_head_id: str, 必填, 族长ID
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: dict, 响应数据
            - id: str, 新创建的家庭ID
    
    状态码说明:
        - 200: 创建成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
        - 3002: 族长不存在
    """
    data = request.get_json()
    if not data:
        return Response.error(400, "请求参数不能为空")
    
    required_fields = ['name', 'clan_head_id']
    for field in required_fields:
        if not data.get(field):
            return Response.error(400, f"{field}不能为空")
    
    # Check if clan head exists
    clan_head = db.fetch_one(
        "SELECT id, name FROM family_user_tab WHERE id = %s AND is_delete = 0",
        (data['clan_head_id'],)
    )
    
    if not clan_head:
        return Response.error(3002, "小族长不存在")
    
    # Generate family ID
    family_id = str(uuid.uuid4())[:16]
    
    # Insert family into database
    family_query = """
        INSERT INTO family_tab (id, name, clan_head_id, clan_head_name)
        VALUES (%s, %s, %s, %s)
    """
    family_params = (family_id, data['name'], clan_head['id'], clan_head['name'])
    
    if not db.execute_query(family_query, family_params):
        return Response.error(500, "创建家庭失败")
    
    # Add clan head to family_person_relation_tab
    relation_id = str(uuid.uuid4())[:16]
    relation_query = """
        INSERT INTO family_person_relation_tab (id, family_id, person_id, relation_type)
        VALUES (%s, %s, %s, %s)
    """
    relation_params = (relation_id, family_id, clan_head['id'], "小族长")
    
    if not db.execute_query(relation_query, relation_params):
        return Response.error(500, "添加小族长到家庭失败")
    
    return Response.success({"id": family_id}, "创建家庭成功")

@bp.route('/add_person', methods=['POST'])
def add_person_to_family():
    """
    添加族人到家庭接口
    
    请求方式: POST
    请求URL: /family/add_person
    
    请求参数 (JSON):
        - family_id: str, 必填, 家庭ID
        - person_id: str, 必填, 族人ID
        - relation_type: str, 可选, 成员类型，默认"正式成员"
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: None
    
    状态码说明:
        - 200: 添加成功
        - 400: 请求参数错误
        - 404: 家庭或族人不存在
        - 500: 服务器内部错误
    """
    data = request.get_json()
    if not data:
        return Response.error(400, "请求参数不能为空")
    
    required_fields = ['family_id', 'person_id']
    for field in required_fields:
        if not data.get(field):
            return Response.error(400, f"{field}不能为空")
    
    # Check if family exists
    family = db.fetch_one(
        "SELECT id FROM family_tab WHERE id = %s",
        (data['family_id'],)
    )
    
    if not family:
        return Response.error(404, "家庭不存在")
    
    # Check if person exists
    person = db.fetch_one(
        "SELECT id FROM family_user_tab WHERE id = %s AND is_delete = 0",
        (data['person_id'],)
    )
    
    if not person:
        return Response.error(404, "族人不存在")
    
    # Check if relation already exists
    existing_relation = db.fetch_one(
        "SELECT id FROM family_person_relation_tab WHERE family_id = %s AND person_id = %s",
        (data['family_id'], data['person_id'])
    )
    
    if existing_relation:
        return Response.error(400, "该族人已在家庭中")
    
    # Generate relation ID
    relation_id = str(uuid.uuid4())[:16]
    relation_type = data.get('relation_type', "正式成员")
    
    # Insert relation into database
    query = """
        INSERT INTO family_person_relation_tab (id, family_id, person_id, relation_type)
        VALUES (%s, %s, %s, %s)
    """
    params = (relation_id, data['family_id'], data['person_id'], relation_type)
    
    if not db.execute_query(query, params):
        return Response.error(500, "添加族人到家庭失败")
    
    return Response.success(None, "添加族人到家庭成功")

@bp.route('/person_list', methods=['POST'])
def get_family_person_list():
    """
    获取家庭成员列表接口
    
    请求方式: POST
    请求URL: /family/person_list
    
    请求参数 (JSON):
        - family_id: str, 必填, 家庭ID
        - display_mode: str, 可选, 显示模式，默认"tree"
            - tree: 树形结构展示
            - list: 列表结构展示
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: dict, 响应数据
            - family_info: dict, 家庭信息
                - id: str, 家庭ID
                - name: str, 家庭名称
            - members: list, 成员列表
                - 树形模式: 嵌套结构，包含children字段
                - 列表模式: 扁平结构，包含id、name、generation、relation_type字段
    
    状态码说明:
        - 200: 获取成功
        - 400: 请求参数错误
        - 404: 家庭不存在
        - 500: 服务器内部错误
    """
    data = request.get_json()
    if not data or not data.get('family_id'):
        return Response.error(400, "家庭ID不能为空")
    
    family_id = data['family_id']
    display_mode = data.get('display_mode', 'tree')  # tree or list
    
    # Check if family exists
    family = db.fetch_one(
        "SELECT id, name FROM family_tab WHERE id = %s",
        (family_id,)
    )
    
    if not family:
        return Response.error(404, "家庭不存在")
    
    # Get all family members
    members = db.fetch_all("""
        SELECT fpr.family_id, fpr.person_id, fpr.relation_type,
               fu.id, fu.name, fu.father_id, fu.mother_id, fu.generation
        FROM family_person_relation_tab fpr
        JOIN family_user_tab fu ON fpr.person_id = fu.id
        WHERE fpr.family_id = %s AND fu.is_delete = 0
        ORDER BY fu.generation, fu.id
    """, (family_id,))
    
    if display_mode == 'list':
        # Return list format
        member_list = []
        for member in members:
            member_info = {
                "id": member['id'],
                "name": member['name'],
                "generation": member['generation'],
                "relation_type": member['relation_type']
            }
            member_list.append(member_info)
        
        return Response.success(
            {
                "family_info": {
                    "id": family['id'],
                    "name": family['name']
                },
                "members": member_list
            },
            "获取家庭族人列表成功"
        )
    else:
        # Return tree format
        # Create a map for quick lookup
        member_map = {}
        for member in members:
            member_id = member['id']
            member_map[member_id] = {
                "id": member_id,
                "name": member['name'],
                "generation": member['generation'],
                "children": []
            }
        
        # Build tree structure
        tree_members = []
        for member in members:
            member_id = member['id']
            father_id = member['father_id']
            
            if father_id and father_id in member_map:
                # Add to father's children list
                member_map[father_id]['children'].append(member_map[member_id])
            else:
                # Top-level member
                tree_members.append(member_map[member_id])
        
        return Response.success(
            {
                "family_info": {
                    "id": family['id'],
                    "name": family['name']
                },
                "members": tree_members
            },
            "获取家庭族人列表成功"
        )
