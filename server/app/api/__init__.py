# -*- coding: utf-8 -*-
"""
API接口包初始化文件

该包包含了家庭树应用的所有API接口模块，用于处理前端请求与后端数据交互。

模块说明：
- auth: 处理用户认证相关接口（注册、登录）
- person: 处理族人信息相关接口（增删改查、列表、详情）
- family: 处理家庭信息相关接口（家庭列表、创建、添加成员）
- home: 处理首页统计数据相关接口
"""

from . import auth, person, family, home
