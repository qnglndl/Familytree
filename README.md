<!--
 * @Author: qnglndl fhfhfhfu114514@163.com
 * @Date: 2025-12-21 08:34:44
 * @LastEditors: qnglndl fhfhfhfu114514@163.com
 * @LastEditTime: 2025-12-21 09:11:03
 * @FilePath: /Familytree/README.md
-->
# 前言
## 欢迎阅读本文档！
### 该文档是关于孔氏家族记录程序的文档
# server文件夹说明
## 要把.env.txt改为.env，不然程序无法运行！
### 语言:python 
### 库:Flask(2.3.3),Flask-CORS(4.0.0),PyJWT(2.8.0),pymysql(01.1.0),cryptography(41.0.4),python-dotenv(1.0.0)
# 下列命令要在server目录下执行！
### 安装命令
```shell(windows)
myenv\Scripts\activate
pip install -r requirements.txt
```
```shell(linnux/mac)
source venv/bin/activate
pip install -r requirements.txt
```
### 启动命令
```shell(windows)
myenv\Scripts\activate
python app.py
```
```shell(linux/mac)
source venv/bin/activate
python app.py
```
### 退出虚拟环境
```shell
deactivate
```
### post命令
#### 注册
```shell
curl -X POST http://server_ip:5001/api/auth/register -H "Content-Type: application/json" -d '{"account": "your_account","password": "your_password","name": "your_name",
"phone": "your_phone"}'
```
#### 登录
```shell
curl -X POST http://server_ip:5001/api/auth/login -H "Content-Type: application/json" -d '{"account": "your_account","password": "your_password"}'
```
#### 添加族人
```shell
curl -X POST http://server_ip:5001/api/person/add -H "Authorization: Bearer <your_token>" -H "Content-Type: application/json" -d '{"name": "your_name","father_id": "0/1","gender": "0/1","birth_date": "your_birth_date(YYYY-MM-DD)","area": "your_area"}'
```
#### 查询族人列表（分页）
```shell
curl -X POST http://server_ip:5001/api/person/list -H "Authorization: Bearer <your_token>" -H "Content-Type: application/json" -d '{"page": 1,"page_size": 10}'
```
#### 查询族人详情
```shell
curl -X POST http://server_ip:5001/api/person/detail -H "Authorization: Bearer <your_token>" -H "Content-Type: application/json" -d '{"id": "your_id"}'
```
# 正文

## 文件介绍

### [app.py](./app.py)
此文件为主程序  
文件里的注释相当详细，无需多言

### [check_db_tables.py](./check_db_tables.py)
这个文件负责连接MySQL库  
然后进行数据库表结构检查

### [debug_db_error.py](./debug_db_error.py)
这个文件负责连接MySQL库  
然后追踪MySQL库的错误

### [simple_db_check.py](./simple_db_check.py)
这个文件负责连接MySQL库   
然后进行简单数据库表检查

### [test_db_connection.py](./test_db_connection.py)
这个文件负责连接MySQL库  
然后进行数据库连接测试

### [test_db_tool.py](./test_db_tool.py)
这个文件负责连接MySQL库  
然后进行数据库工具类测试

### [app/utils/db.py](./app/utils/db.py)
这个文件负责连接MySQL库  
然后进行查询

### [app/utils/jwt.py](./app/utils/jwt.py)
这个文件负责连接MySQL库  
然后进行生成和验证 JWT 令牌

### [app/utils/password.py](./app/utils/password.py)
这个文件负责连接MySQL库  
然后进行对密码的哈希处理

### [app/api/auth.py](./app/api/auth.py)
该模块处理家庭树应用的用户认证相关接口，包括用户注册和登录功能  
文件里的注释相当详细，无需多言

### [app/api/family.py](./app/api/family.py)
该模块处理家庭树应用的家庭信息相关接口，包括家庭列表查询、创建家庭、添加成员等功能  
文件里的注释相当详细，无需多言

### [app/api/home.py](./app/api/home.py)
获取主页统计数据,好不知道干嘛的

### [app/api/person.py](./app/api/person.py)
该模块处理家庭树应用的族人信息相关接口，包括族人列表查询、详情查询、添加、更新和删除等功能  
文件里的注释相当详细，无需多言

### [app/api/user.py](./app/api/user.py)
该模块处理家庭树应用的用户管理相关接口，包括用户列表查询、编辑、禁用/启用、重置密码和新增用户功能  
文件里的注释相当详细，无需多言


# client文件夹说明
### 语言:python,html,js
### python库:blinker(1.9.0)click(8.3.1)Flask(3.1.2)itsdangerous(2.2.0)Jinja2(3.1.6)MarkupSafe(3.0.3)Werkzeug(3.1.4)

# 下列命令要在client目录下执行！
### 安装命令
```shell(windows)
myenv\Scripts\activate
pip install -r requirements.txt
```
```source venv/bin/activate
shell(linux/mac)
source venv/bin/activate
pip install -r requirements.txt
```
### 启动命令
```shell(windows)
myenv\Scripts\activate
python app.py
```
```shell(linux/mac)
source venv/bin/activate
python app.py
```
### 退出虚拟环境
```shell
deactivate
```

# 正文
## 文件介绍
## python类
### [app.py](./app.py)
文件里很详细的，不多赘述

## html类
### [login.html](./templates/login.html)
登录页面，css样式直接整合进去了

### [register.html](./templates/register.html)
注册页面，css样式直接整合进去了

## js类
### [login.js](./static/js/login.js)
发送post请求去后台，用于登录

### [register.js](./static/js/register.js)
发送post请求去后台，用于注册

# 后记
制作人员名单：孔焕彬(server)、孔思勋(client)  
至于为啥所有文件里的作者同一个人，那规范文件的不就是一个人吗  
做这玩意要死要活的＞﹏＜我太难了/(ㄒoㄒ)/~~
