(function(){
  const tip = document.getElementById('loginTip');
  const nicknameEl = document.getElementById('nickname');
  const passwordEl = document.getElementById('password');
  const serverSelect = document.getElementById('serverSelect');
  const form = document.getElementById('loginForm');

  // 加载服务器列表
  fetch('/config').then(r=>r.json()).then(data=>{
    let servers = (data && Array.isArray(data.servers)) ? data.servers : [];
    const isHttps = location.protocol === 'https:';
    // 过滤协议：HTTPS 仅 wss，HTTP 显示 ws/wss
    servers = servers.filter(u => isHttps ? /^wss:\/\//i.test(u) : (/^ws:\/\//i.test(u) || /^wss:\/\//i.test(u)) );
    // 去重：按主机名优先选择 wss 版本
    const seenHost = new Set();
    const sorted = servers.slice().sort((a,b)=>{ const aw = /^wss:\/\//i.test(a)?1:0; const bw = /^wss:\/\//i.test(b)?1:0; return bw - aw; });
    const finalServers = [];
    sorted.forEach(u=>{ try{ const host = new URL(u).hostname; if(!seenHost.has(host)){ seenHost.add(host); finalServers.push(u); } }catch{ /* ignore */ } });
    if (finalServers.length === 0) {
      tip.textContent = isHttps ? '当前为 HTTPS 页面，请选择 wss:// 服务器地址' : '请选择服务器地址';
    }
    // 友好名称：本地服务器 / 公共服务器1 / 公共服务器2
    let publicIdx = 0;
    finalServers.forEach(url=>{
      let label = '服务器';
      try{
        const u = new URL(url);
        const host = u.hostname;
        if (host === 'localhost' || host === '127.0.0.1'){
          label = '本地服务器';
        } else {
          publicIdx += 1;
          label = `公共服务器${publicIdx}`;
        }
      }catch{}
      const opt = document.createElement('option');
      opt.value = url; opt.textContent = label;
      serverSelect.appendChild(opt);
    });
  }).catch(()=>{
    tip.textContent = '加载服务器列表失败，请稍后重试';
  });

  function validate(){
    const nick = nicknameEl.value.trim();
    const pass = passwordEl.value;
    const server = serverSelect.value.trim();
    if(!nick){ tip.textContent = '请输入昵称'; return false; }
    if(!pass){ tip.textContent = '请输入密码'; return false; }
    if(pass !== '123456'){ tip.textContent = '密码错误（固定密码：123456）'; return false; }
    if(!server){ tip.textContent = '请选择服务器地址'; return false; }
    tip.textContent = ''; return true;
  }

  form.addEventListener('submit', function(e){
    e.preventDefault();
    if(!validate()) return;
    const params = new URLSearchParams({ u: nicknameEl.value.trim(), room: 'manbo', ws: serverSelect.value.trim() });
    location.href = '/chat?' + params.toString();
  });
})();