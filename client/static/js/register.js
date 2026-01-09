<<<<<<< HEAD
/*
 * @Author: git config qnglndl && git config fhfhfhfu114514@163.com
 * @Date: 2025-12-20 08:44:50
 * @LastEditors: qnglndl fhfhfhfu114514@163.com
 * @LastEditTime: 2025-12-21 06:26:58
 * @FilePath: /client/static/js/register.js
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

document.getElementById('regBtn').addEventListener('click', async () => {
    const name     = document.getElementById('name').value.trim();
    const phone    = document.getElementById('phone').value.trim();
    const account  = document.getElementById('account').value.trim();
    const password = document.getElementById('password').value;
    const errMsg   = document.getElementById('errMsg');

    if (!name || !phone || !account || !password) {
        errMsg.textContent = '所有字段均不能为空';
        return;
    }

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, phone, account, password })
        });
        const data = await res.json();

    if (res.ok && data.code === 200 && data.data?.token) {
        localStorage.setItem('jwt', data.data.token);
        localStorage.setItem('uid', String(data.data.userInfo.id));
        location.href = '/home';
    } else {
        errMsg.textContent = data.message || '注册失败';
    }
    } catch (e) {
        errMsg.textContent = '网络或服务器错误';
        console.error(e);
    }
});
=======
/*
 * @Author: git config qnglndl && git config fhfhfhfu114514@163.com
 * @Date: 2025-12-20 08:44:50
 * @LastEditors: qnglndl fhfhfhfu114514@163.com
 * @LastEditTime: 2025-12-21 06:26:58
 * @FilePath: /client/static/js/register.js
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

(async () => {
    // 服务器地址直接写死为 127.0.0.1:5001
    let serverIp = '127.0.0.1:5001';

    const regBtn = document.getElementById('regBtn');
    regBtn.addEventListener('click', async () => {
        const name     = document.getElementById('name').value.trim();
        const phone    = document.getElementById('phone').value.trim();
        const account  = document.getElementById('account').value.trim();
        const password = document.getElementById('password').value;
        const errMsg   = document.getElementById('errMsg');

        if (!name || !phone || !account || !password) {
            errMsg.textContent = '所有字段均不能为空';
            return;
        }

        try {
            const res = await fetch(`http://${serverIp}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, phone, account, password })
            });
            const data = await res.json();

            if (data.success && data.data && data.data.token) {
                localStorage.setItem('jwt', data.data.token);
                window.location.href = '/home';
            } else {
                errMsg.textContent = data.message || '注册失败';
            }
        } catch (e) {
            errMsg.textContent = '网络或服务器错误';
            console.error(e);
        }
    });
})();
>>>>>>> 1bcaf920976e2fc74811380659523f8f88e4a167
