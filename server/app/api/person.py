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
族人信息API模块

该模块处理家庭树应用的族人信息相关接口，包括族人列表查询、详情查询、添加、更新和删除等功能。
支持多条件筛选和分页查询，为前端提供完整的族人信息管理能力。

依赖模块：
- Flask: Web框架，用于创建API接口
- Response: 自定义响应类，统一API返回格式
- db: 数据库操作工具，用于数据库交互
- uuid: 用于生成唯一族人ID
"""

from typing import Any
from flask import Blueprint, request, jsonify
from app import Response
from app.utils.db import db
import uuid

# 创建Flask蓝图，定义族人相关的API路由
bp = Blueprint('person', __name__)

@bp.route('/list', methods=['POST'])
def get_person_list():
    """
    获取族人列表接口
    
    请求方式: POST
    请求URL: /person/list
    
    # 请求参数 (JSON):
        - search_text: str, 可选, 搜索文本，用于模糊查询族人ID、姓名和小名
        - page: int, 可选, 当前页码，默认1
        - page_size: int, 可选, 每页数量，默认10
        - no_pagination: bool, 可选, 是否不分页，默认false，设置为true时返回所有符合条件的记录
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: dict, 响应数据
            - total: int, 总记录数
            - list: list, 族人列表
                - id: str, 族人ID
                - name: str, 姓名
                - daily_name: str, 小名
                - father_name: str, 父亲姓名
                - mother_name: str, 母亲姓名
                - generation: str, 世代
                - gender: str, 性别
                - is_alive: int, 是否在世（0：否，1：是）
                - children_count: int, 子女数量
                - remark: str, 备注
    
    状态码说明:
        - 200: 获取成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
    """
    data = request.get_json() or {}
    
    # Build query conditions
    conditions = []
    params = []
    
    # Add search_text condition
    search_text = data.get('search_text')
    if search_text:
        conditions.append("(id LIKE %s OR name LIKE %s OR daily_name LIKE %s)")
        search_pattern = f"%{search_text}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    # Add is_delete condition
    conditions.append("is_delete = 0")
    
    # Build WHERE clause
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Get total count
    count_query = f"SELECT COUNT(id) FROM family_user_tab {where_clause}"
    total = db.fetch_scalar(count_query, tuple(params)) or 0
    
    # Check if pagination is disabled
    no_pagination = data.get('no_pagination', False)
    
    # Pagination
    if no_pagination:
        # No pagination - return all results
        query = f"""
            SELECT id, name, daily_name, father_name, mother_name, lineage, gender, is_alive,remark
            FROM family_user_tab
            {where_clause}
            ORDER BY CAST(id AS UNSIGNED)
        """
    else:
        # With pagination
        page = data.get('page', 1)
        page_size = data.get('page_size', 10)
        offset = (page - 1) * page_size
        
        query = f"""
            SELECT id, name, daily_name, father_name, mother_name, lineage, gender, is_alive,remark
            FROM family_user_tab
            {where_clause}
            ORDER BY CAST(id AS UNSIGNED)
            LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
    
    persons = db.fetch_all(query, tuple(params))
    
    # Get children count for each person
    for person in persons:
        children_count = db.fetch_scalar(
            "SELECT COUNT(id) FROM family_user_tab WHERE father_id = %s AND is_delete = 0",
            (person['id'],)
        ) or 0
        person['children_count'] = children_count
    
    return Response.success(
        {
            "total": total,
            "list": persons
        },
        "获取族人列表成功"
    )

@bp.route('/detail', methods=['POST'])
def get_person_detail():
    """
    获取族人详情接口
    
    请求方式: POST
    请求URL: /person/detail
    
    请求参数 (JSON):
        - id: str, 必填, 族人ID
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: dict, 响应数据
            - id: str, 族人ID
            - name: str, 姓名
            - daily_name: str, 小名
            - father_name: str, 父亲姓名
            - mother_name: str, 母亲姓名
            - generation: str, 世代
            - gender: str, 性别
            - is_alive: int, 是否在世（0：否，1：是）
            - birth_date: str, 出生日期
            - death_date: str, 去世日期
            - area: str, 居住地
            - university: str, 大学
            - spouse: str, 配偶
            - children: list, 子女列表
                - id: str, 子女ID
                - name: str, 子女姓名
                - gender: str, 子女性别
                - generation: str, 子女世代
    
    状态码说明:
        - 200: 获取成功
        - 400: 请求参数错误
        - 404: 族人不存在
        - 500: 服务器内部错误
    """
    data = request.get_json()
    if not data or not data.get('id'):
        return Response.error(400, "族人ID不能为空")
    
    person_id = data['id']
    
    # Get person details
    print(f"Requesting person detail with id: {person_id}, type: {type(person_id)}")
    person = db.fetch_one("""
        SELECT * FROM family_user_tab WHERE id = %s AND (is_delete = 0 OR is_delete is null)
    """, (person_id,))
    
    print(f"Query result: {person}")
    
    if not person:
        return Response.error(404, "族人不存在")
    
    # Get children list
    children = db.fetch_all("""
        SELECT id, name, daily_name, spouse,gender, lineage,remark FROM family_user_tab 
        WHERE father_id = %s AND (is_delete = 0 OR is_delete is null)
        ORDER BY id
    """, (person_id,))
    
    # Format response data
    person_data = {
        **person,
        "children": children
    }
    
    return Response.success(person_data, "获取族人详情成功")

@bp.route('/add', methods=['POST'])
def add_person():
    """
    添加新族人接口
    
    请求方式: POST
    请求URL: /person/add
    
    请求参数 (JSON):
        - name: str, 必填, 姓名
        - daily_name: str, 可选, 小名
        - cell_position: str, 可选, 格子位置
        - lineage: str, 可选, 谱系
        - father_name: str, 可选, 父亲姓名
        - father_id: str, 可选, 父亲ID
        - mother_name: str, 可选, 母亲姓名
        - mother_id: str, 可选, 母亲ID
        - bitrh_father_name: str, 可选, 亲生父亲姓名
        - birth_father_id: str, 可选, 亲生父亲ID
        - remark: str, 可选, 备注
        - is_adopted: int, 可选, 是否领养（0：否，1：是）
        - adopted_id: str, 可选, 领养ID
        - is_stepchild: int, 可选, 是否继子（0：否，1：是）
        - stepchild_id: str, 可选, 继子ID
        - is_xianpu: int, 可选, 是否显谱（0：否，1：是）
        - birth_info: str, 可选, 出生信息
        - death_info: str, 可选, 去世信息
        - gender: str, 可选, 性别
        - area: str, 可选, 居住地
        - birth_date: str, 可选, 出生日期
        - death_date: str, 可选, 去世日期
        - is_alive: int, 可选, 是否在世（0：否，1：是）
        - generation: str, 可选, 世代
        - university: str, 可选, 大学
        - spouse: str, 可选, 配偶
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: dict, 响应数据
            - id: str, 新添加的族人ID
    
    状态码说明:
        - 200: 添加成功
        - 400: 请求参数错误
        - 500: 服务器内部错误
    """
    data = request.get_json()
    if not data:
        return Response.error(400, "请求参数不能为空")
    
    # 检查必填字段
    if not data.get('name'):
        return Response.error(400, "姓名不能为空")
    if not data.get('father_id'):
        return Response.error(400, "父亲不能为空")
    
    # 检查是否存在相同father_id和name的记录
    check_query = """
        SELECT id, name, daily_name
        FROM family_user_tab
        WHERE father_id = %s AND name = %s AND is_delete = 0
    """
    existing_person = db.fetch_one(check_query, (data['father_id'], data['name']))
    
    if existing_person:
        return Response.error(409, "族人已存在", existing_person)
    
    # 获取父亲姓名
    father_name = db.fetch_one(
        "SELECT name FROM family_user_tab WHERE id = %s AND is_delete = 0",
        (data['father_id'],)
    )
    # Generate person ID
    person_id = str(uuid.uuid4())[:16]
    
    # Build insert query
    columns = ['id', 'name','father_name']
    values = [person_id, data['name'], father_name['name']]
    
    # Add optional fields
    optional_fields = [
        'daily_name', 'cell_position', 'lineage', 'father_id',
        'mother_name', 'mother_id', 'bitrh_father_name', 'birth_father_id',
        'remark', 'is_adopted', 'adopted_id', 'is_stepchild', 'stepchild_id',
        'is_xianpu', 'birth_info', 'death_info', 'gender', 'area', 'birth_date',
        'death_date', 'is_alive', 'generation', 'university', 'spouse'
    ]
    
    for field in optional_fields:
        if field in data:
            columns.append(field)
            values.append(data[field])
    
    # Add default values
    columns.append('is_delete')
    values.append(0)
    
    # Build query string
    columns_str = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(values))
    
    query = f"""
        INSERT INTO family_user_tab ({columns_str})
        VALUES ({placeholders})
    """
    
    if not db.execute_query(query, tuple[Any, ...](values)):
        return Response.error(500, "新增族人失败")
    
    return Response.success({"id": person_id}, "新增族人成功")

@bp.route('/update', methods=['POST'])
def update_person():
    """
    更新族人信息接口
    
    请求方式: POST
    请求URL: /person/update
    
    请求参数 (JSON):
        - id: str, 必填, 族人ID
        - name: str, 可选, 姓名
        - daily_name: str, 可选, 小名
        - cell_position: str, 可选, 格子位置
        - lineage: str, 可选, 谱系
        - father_name: str, 可选, 父亲姓名
        - father_id: str, 可选, 父亲ID
        - mother_name: str, 可选, 母亲姓名
        - mother_id: str, 可选, 母亲ID
        - bitrh_father_name: str, 可选, 亲生父亲姓名
        - birth_father_id: str, 可选, 亲生父亲ID
        - remark: str, 可选, 备注
        - is_adopted: int, 可选, 是否领养（0：否，1：是）
        - adopted_id: str, 可选, 领养ID
        - is_stepchild: int, 可选, 是否继子（0：否，1：是）
        - stepchild_id: str, 可选, 继子ID
        - is_xianpu: int, 可选, 是否显谱（0：否，1：是）
        - birth_info: str, 可选, 出生信息
        - death_info: str, 可选, 去世信息
        - gender: str, 可选, 性别
        - area: str, 可选, 居住地
        - birth_date: str, 可选, 出生日期
        - death_date: str, 可选, 去世日期
        - is_alive: int, 可选, 是否在世（0：否，1：是）
        - generation: str, 可选, 世代
        - university: str, 可选, 大学
        - spouse: str, 可选, 配偶
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: None
    
    状态码说明:
        - 200: 更新成功
        - 400: 请求参数错误或没有需要更新的字段
        - 404: 族人不存在
        - 500: 服务器内部错误
    """
    data = request.get_json()
    if not data or not data.get('id'):
        return Response.error(400, "族人ID不能为空")
    
    person_id = data['id']
    
    # Check if person exists
    existing_person = db.fetch_one(
        "SELECT id FROM family_user_tab WHERE id = %s AND is_delete = 0",
        (person_id,)
    )
    
    if not existing_person:
        return Response.error(404, "族人不存在")
    
    # Build update query
    update_fields = []
    update_values = []
    
    fields_to_update = [
        'name', 'daily_name', 'cell_position', 'lineage', 'father_name', 'father_id',
        'mother_name', 'mother_id', 'bitrh_father_name', 'birth_father_id',
        'remark', 'is_adopted', 'adopted_id', 'is_stepchild', 'stepchild_id',
        'is_xianpu', 'birth_info', 'death_info', 'gender', 'area', 'birth_date',
        'death_date', 'is_alive', 'generation', 'university', 'spouse'
    ]
    
    for field in fields_to_update:
        if field in data:
            update_fields.append(f"{field} = %s")
            update_values.append(data[field])
    
    if not update_fields:
        return Response.error(400, "没有需要更新的字段")
    
    update_fields_str = ', '.join(update_fields)
    update_values.append(person_id)
    
    query = f"""
        UPDATE family_user_tab
        SET {update_fields_str}
        WHERE id = %s AND is_delete = 0
    """
    
    if not db.execute_query(query, tuple(update_values)):
        return Response.error(500, "更新族人失败")
    
    return Response.success(None, "更新族人成功")

@bp.route('/delete', methods=['POST'])
def delete_person():
    """
    删除族人接口（软删除）
    
    请求方式: POST
    请求URL: /person/delete
    
    请求参数 (JSON):
        - id: str, 必填, 族人ID
    
    响应参数:
        - success: bool, 请求是否成功
        - code: int, 响应状态码
        - message: str, 响应消息
        - data: None
    
    状态码说明:
        - 200: 删除成功
        - 400: 请求参数错误
        - 404: 族人不存在
        - 500: 服务器内部错误
        - 2002: 该族人有子女，无法删除
    
    注意事项:
        - 该接口采用软删除方式，将is_delete字段设置为1
        - 如果族人有子女，将无法删除，需要先删除或处理子女关系
    """
    data = request.get_json()
    if not data or not data.get('id'):
        return Response.error(400, "族人ID不能为空")
    
    person_id = data['id']
    
    # Check if person has children
    children_count = db.fetch_scalar(
        "SELECT COUNT(id) FROM family_user_tab WHERE father_id = %s AND is_delete = 0",
        (person_id,)
    ) or 0
    
    if children_count > 0:
        return Response.error(2002, "该族人有子女，无法删除")
    
    # Soft delete person
    query = """
        UPDATE family_user_tab
        SET is_delete = 1
        WHERE id = %s AND is_delete = 0
    """
    
    if not db.execute_query(query, (person_id,)):
        return Response.error(500, "删除族人失败")
    
    return Response.success(None, "删除族人成功")
