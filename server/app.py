# -*- coding: utf-8 -*-
"""
家庭树应用后端主入口文件

该文件负责初始化Flask应用，配置跨域资源共享(CORS)，设置全局token验证中间件，
注册各个API蓝图，并启动服务器。
"""

import sys
import io

# 强制标准输出/错误使用UTF8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 导入Flask核心模块，用于创建应用和处理HTTP请求
from flask import Flask, request, jsonify
# 导入CORS扩展，用于处理跨域资源共享
from flask_cors import CORS
# 导入自定义响应类，用于统一API返回格式
from app import Response
# 导入数据库操作工具类实例
from app.utils.db import db
# 导入JWT管理器实例，用于token的生成和验证
from app.utils.jwt import jwt_manager
# 导入os模块，用于访问操作系统功能（如环境变量）
import os
# 导入dotenv模块，用于加载.env文件中的环境变量
from dotenv import load_dotenv

# 加载.env文件中的环境变量到系统环境变量中
load_dotenv()

# 创建Flask应用实例，__name__表示当前模块名，用于确定应用根目录
app = Flask(__name__)

# 配置跨域资源共享
# resources参数指定只有/api/*路径下的接口允许跨域请求
# origins="*"表示允许所有来源的跨域请求
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 定义全局token验证中间件
# @app.before_request装饰器表示该函数会在每个请求处理前执行
@app.before_request
def verify_token():
    # 跳过登录和注册接口的token验证（这些接口需要公开访问）
    if request.path in ["/api/auth/login", "/api/auth/register"]:
        return None
    
    # 跳过非API接口的token验证（如静态文件等）
    if not request.path.startswith("/api/"):
        return None
    
    # 从请求头中获取Authorization字段（通常包含Bearer token）
    token = request.headers.get("Authorization")
    # 检查是否提供了token
    if not token:
        # 如果没有token，返回401未授权错误
        return Response.error(401, "未授权，请先登录")
    
    # 移除token中的"Bearer "前缀（如果存在）
    if token.startswith("Bearer "):
        token = token[7:]
    
    # 调用JWT管理器验证token的有效性
    verify_result = jwt_manager.verify_token(token)
    # 检查token验证结果
    if not verify_result["valid"]:
        # 如果token无效，返回401错误并包含具体错误信息
        return Response.error(401, verify_result["message"])
    
    # 将验证通过的用户ID存储在请求上下文中，供后续处理函数使用
    request.user_id = verify_result["user_id"]
    # 验证通过，继续处理请求
    return None

# 导入各个API模块的蓝图
from app.api import auth, person, family, home, user

# 注册认证相关的API蓝图，前缀为/api/auth
app.register_blueprint(auth.bp, url_prefix="/api/auth")
# 注册族人信息相关的API蓝图，前缀为/api/person
app.register_blueprint(person.bp, url_prefix="/api/person")
# 注册家族信息相关的API蓝图，前缀为/api/family
app.register_blueprint(family.bp, url_prefix="/api/family")
# 注册首页相关的API蓝图，前缀为/api/home
app.register_blueprint(home.bp, url_prefix="/api/home")
# 注册用户管理相关的API蓝图，前缀为/api/user
app.register_blueprint(user.bp, url_prefix="/api/user")

# 定义健康检查接口，用于监控服务状态
@app.route("/api/health")
def health_check():
    # 返回成功响应，包含服务状态信息
    return Response.success({
        "status": "ok",  # 服务状态正常
        "message": "Family Tree API is running"  # 服务运行中消息
    })

# 应用入口点检查
if __name__ == "__main__":
    print(r'''
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
''')
    print("=== 所有页面路径 ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.methods} {rule}")

    # 从环境变量获取服务器端口，如果未设置则使用默认端口5000
    port = int(os.getenv("SERVER_PORT", 5000))
    # 启动Flask服务器
    # host="0.0.0.0"表示监听所有网络接口（允许外部访问）
    # port=port指定服务器端口
    # debug=True开启调试模式（开发环境使用）
    app.run(host="::", port=port, debug=True)
    print("=== Registered routes ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.methods} {rule}")
