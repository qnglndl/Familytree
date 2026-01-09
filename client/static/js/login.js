/*
 * @Author: qnglndl fhfhfhfu114514@163.com
 * @Date: 2025-12-20 06:49:37
 * @LastEditors: qnglndl fhfhfhfu114514@163.com
 * @LastEditTime: 2025-12-21 06:15:04
 * @FilePath: /client/static/js/login.js
 */
/*
 *                        _oo0oo_
 *                       o8888888o
 *                       88" . "88
 *                       (| -_- |)
 *                       0\  =  /0
 *                     ___/`---'\___
 *                   .' \\|     |// '.
 *                  / \\|||  :  |||// \
 *                 / _||||| -:- |||||- \
 *                |   | \\\  - /// |   |
 *                | \_|  ''\---/''  |_/ |
 *                \  .-\__  '-'  ___/-. /
 *              ___'. .'  /--.--\  `. .'___
 *           ."" '<  `.___\_<|>_/___.' >' "".
 *          | | :  `- \`.;`\ _ /`;.`/ - ` : | |
 *          \  \ `_.   \_ __\ /__ _/   .-` /  /
 *      =====`-.____`.___ \_____/___.-`___.-'=====
 *                        `=---='
 * 
 * 
 *      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * 
 *            佛祖保佑     永不宕机     永无BUG
 * 
 *        佛曰:  
 *                写字楼里写字间，写字间里程序员；  
 *                程序人员写程序，又拿程序换酒钱。  
 *                酒醒只在网上坐，酒醉还来网下眠；  
 *                酒醉酒醒日复日，网上网下年复年。  
 *                但愿老死电脑间，不愿鞠躬老板前；  
 *                奔驰宝马贵者趣，公交自行程序员。  
 *                别人笑我忒疯癫，我笑自己命太贱；  
 *                不见满街漂亮妹，哪个归得程序员？
 */

document.getElementById('loginBtn').addEventListener('click', async () => {
    const account = document.getElementById('account').value.trim();
    const password = document.getElementById('password').value;
    const errMsg = document.getElementById('errMsg');

    if (!account || !password) {
        errMsg.textContent = '账号和密码不能为空';
        return;
    }

    try {
        const res = await fetch('http://127.0.0.1:5001/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account, password })
        });
        const data = await res.json();

        if (data.success && data.data && data.data.token) {
            // 存储 token 并跳转
            localStorage.setItem('jwt', data.data.token);
            window.location.href = '/home';
        } else {
            errMsg.textContent = data.message || '登录失败';
        }
    } catch (e) {
        errMsg.textContent = '网络或服务器错误';
        console.error(e);
    }
});
