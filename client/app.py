'''
Author: qnglndl fhfhfhfu114514@163.com
Date: 2025-12-20 05:57:17
LastEditors: qnglndl fhfhfhfu114514@163.com
LastEditTime: 2025-12-21 06:32:03
FilePath: /client/app.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''


from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import re

app = Flask(__name__)

# 假设远端 API 的基地址，实际部署时改为你自己的域名
with open("server_ip.txt", "r", encoding="utf-8") as f:
    server_ip = f.readline().strip()
    REMOTE_API_BASE = server_ip # 仅示例，真实地址请替换

# 提取主机名用于后续检查
match = re.search(r'(?<=://)([^:/\[\]]+|\[[^\]]+\])', REMOTE_API_BASE)
host = match.group(1).strip('[]') if match else None

@app.route("/")
def index():
    """根地址：若未登录则跳登录页，否则跳 /home（演示用）"""
    # 简单判断：前端会把 token 存 localStorage，这里只做后端占位
    return render_template("index.html")

@app.route("/login")
def login_page():
    """纯前端登录页"""
    return render_template("login.html")

@app.route("/home")
def home():
    """登录成功后的跳转页，目前仅占位"""
    return "这是族谱首页，后续再开发。"

# 可选：代理接口，用于解决 CORS 或调试
# 如果你的前端直接访问远端 /api/auth/login，可删除此段
@app.route("/api/auth/login", methods=["POST"])
def proxy_login():
    """把本地 /api/auth/login 转发到远端"""
    import requests
    resp = requests.post(
        f"{REMOTE_API_BASE}/api/auth/login",
        json=request.get_json(),
        headers={"Content-Type": "application/json"}
    )
    return jsonify(resp.json()), resp.status_code

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/api/server_ip")
def server_ip():
    try:
        with open("server_ip.txt", "r", encoding="utf-8") as f:
            ip = f.readline().strip()
        return jsonify({"ip": ip})
    except Exception:
        return jsonify({"ip": "localhost"}), 500

if __name__ == "__main__":
    if os.name == "nt":  # Windows
        ret = os.system(f'ping -n 1 {host} >nul')
    else:                # Unix/Linux/macOS
        ret = os.system(f'ping -c 1 {host} > /dev/null')
    if ret != 0:
        print(f"远端服务器({host})无法访问，请检查网络连接或远端服务器状态。")
        exit(1)
    print(r"""
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
 
            佛祖保佑       永不宕机     永无BUG
 
        佛曰:  
                写字楼里写字间，写字间里程序员；  
                程序人员写程序，又拿程序换酒钱。  
                酒醒只在网上坐，酒醉还来网下眠；  
                酒醉酒醒日复日，网上网下年复年。  
                但愿老死电脑间，不愿鞠躬老板前；  
                奔驰宝马贵者趣，公交自行程序员。  
                别人笑我忒疯癫，我笑自己命太贱；  
                不见满街漂亮妹，哪个归得程序员？
 """)
    app.run(debug=True,host="::", port=5000)
