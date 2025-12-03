(function(){
  // 从URL获取用户与ws地址
  const qs = new URLSearchParams(location.search);
  const nickname = qs.get('u') || '匿名';
  const room = qs.get('room') || 'manbo';
  let wsBase = qs.get('ws') || (location.protocol==='https:'? 'wss://' : 'ws://') + location.host + '/ws';
  if (location.protocol === 'https:' && /^ws:\/\//i.test(wsBase)) {
    wsBase = wsBase.replace(/^ws:\/\//i, 'wss://');
  }

  // UI 元素
  const histBtn = document.getElementById('historyBtn');
  const logoutBtn = document.getElementById('logoutBtn');
  const listEl = document.getElementById('messageList');
  const msgInput = document.getElementById('msgInput');
  const sendBtn = document.getElementById('sendBtn');
  const emojiBtns = document.querySelectorAll('[data-emoji]');
  const onlineListEl = document.getElementById('onlineUsersList');
  const onlineCountEl = document.getElementById('onlineCount');
  const emojiToggleBtn = document.getElementById('emojiToggle');
  const emojiPanelEl = document.getElementById('emojiPanel');

  // 建立 WebSocket 连接
  const wsUrl = new URL(wsBase);
  wsUrl.searchParams.set('u', nickname);
  wsUrl.searchParams.set('room', room);
  const ws = new WebSocket(wsUrl.toString());

  function scrollToBottom(){ listEl.scrollTop = listEl.scrollHeight; }
  function escapeHtml(s){ return s.replace(/[&<>]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
  function formatTime(t){ const d=new Date(t); return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`; }

  // 流式 AI 消息缓存：id -> 气泡元素
  const aiBuffers = {};

  // 渲染气泡内容：支持音乐卡片、电影 iframe、AI 流式文本、天气卡片、新闻卡片
  function renderBubbleContent(bubbleEl, m){
    // music 卡片
    if (m.kind === 'music' && m.music && (m.music.url || m.music.image || m.music.name)){
      const name = escapeHtml(m.music.name || '未知歌曲');
      const singer = escapeHtml(m.music.singer || '');
      const image = m.music.image || '';
      const url = m.music.url || '';
      const proxied = url ? `/music_proxy?u=${encodeURIComponent(url)}` : '';
      const card = document.createElement('div');
      card.className = 'music-card';
      card.innerHTML = `
        <div class="music-cover">${image?`<img src="${image}" alt="${name}" />`:''}</div>
        <div class="music-info">
          <div class="music-title">${name}${singer?` - ${singer}`:''}</div>
          <audio class="music-player" controls preload="none" ${proxied?`src="${proxied}"`:''}></audio>
        </div>
      `;
      bubbleEl.appendChild(card);
      return true;
    }
    // movie iframe
    if (m.kind === 'movie' && m.movie && m.movie.iframe){
      const iframe = document.createElement('iframe');
      iframe.src = m.movie.iframe;
      iframe.width = 400;
      iframe.height = 400;
      iframe.frameBorder = 0;
      iframe.allowFullscreen = true;
      bubbleEl.appendChild(iframe);
      return true;
    }
    // weather 卡片
    if (m.kind === 'weather' && m.weather && (m.weather.city || m.weather.cond || m.weather.temp)){
      const w = m.weather;
      const city = escapeHtml(w.city || '未知城市');
      const cond = escapeHtml(w.cond || '');
      const temp = escapeHtml(w.temp || '');
      const high = escapeHtml(w.high || '');
      const low = escapeHtml(w.low || '');
      const humidity = escapeHtml(w.humidity || '');
      const wind = escapeHtml(w.wind || '');
      const aqi = escapeHtml(w.aqi || '');
      const tips = escapeHtml(w.tips || '');
      const ut = escapeHtml(w.update_time || '');
      const card = document.createElement('div');
      card.className = 'weather-card';
      card.innerHTML = `
        <div class="weather-header">
          <div class="city">${city}</div>
          <div class="cond">${cond}</div>
        </div>
        <div class="weather-main">
          <div class="temp">${temp ? `${temp}` : ''}</div>
          <div class="range">${high||low ? `${low ? low+' / ' : ''}${high || ''}` : ''}</div>
        </div>
        <div class="weather-extra">
          ${humidity?`<span>湿度：${humidity}</span>`:''}
          ${wind?`<span>风：${wind}</span>`:''}
          ${aqi?`<span>空气质量：${aqi}</span>`:''}
        </div>
        ${tips?`<div class="weather-tips">${tips}</div>`:''}
        ${ut?`<div class="weather-update">更新：${ut}</div>`:''}
      `;
      bubbleEl.appendChild(card);
      return true;
    }
    // news 卡片
    if (m.kind === 'news' && m.news && Array.isArray(m.news.items)){
      const items = m.news.items;
      const card = document.createElement('div');
      card.className = 'news-card';
      const list = items.map(t => `<li>${escapeHtml(String(t))}</li>`).join('');
      card.innerHTML = `
        <div class="news-header">热点新闻（${escapeHtml(m.news.source||'')})</div>
        <ul class="news-list">${list}</ul>
      `;
      bubbleEl.appendChild(card);
      return true;
    }
    // 默认纯文本
    bubbleEl.textContent = m.text || '';
    return false;
  }

  function appendSystem(text){
    const item = document.createElement('div');
    item.className = 'message system';
    item.innerHTML = `<div class="bubble">${text}</div>`;
    listEl.appendChild(item);
    scrollToBottom();
  }

  // 消息存储（用于过滤显示）
  const allMessages = []; // {from, text, time, self, kind?, music?}

  // 联系人管理
  const contacts = new Map(); // name -> {name}
  let currentPeer = null; // null 表示显示所有消息

  function renderContacts(){
    const list = document.getElementById('contactsList');
    if (!list) return;
    list.innerHTML = '';
    const allItem = document.createElement('div');
    allItem.className = 'contact-item' + (currentPeer === null ? ' active' : '');
    allItem.innerHTML = '<div class="avatar">🌐</div><div>所有消息</div>';
    allItem.onclick = () => { currentPeer = null; renderContacts(); renderMessages(); };
    list.appendChild(allItem);
    for (const name of contacts.keys()){
      const item = document.createElement('div');
      item.className = 'contact-item' + (currentPeer === name ? ' active' : '');
      item.innerHTML = `<div class="avatar">${name.slice(0,1)}</div><div>${name}</div>`;
      item.onclick = () => { currentPeer = name; renderContacts(); renderMessages(); };
      list.appendChild(item);
    }
  }

  function addContact(name){
    const n = (name||'').trim();
    if (!n) return;
    if (contacts.has(n)) { currentPeer = n; renderContacts(); renderMessages(); return; }
    contacts.set(n, {name:n});
    currentPeer = n;
    renderContacts();
  }

  function bindAddContactUI(){
    const btn = document.getElementById('addContactBtn');
    const input = document.getElementById('newContactInput');
    if (!btn || !input) return;
    btn.addEventListener('click', ()=>{ addContact(input.value); input.value=''; });
    input.addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ addContact(input.value); input.value=''; } });
  }

  function renderMessages(){
    const list = document.getElementById('messageList');
    if (!list) return;
    list.innerHTML = '';
    const filtered = allMessages.filter(m => {
      if (currentPeer === null) return true;
      if (m.from === currentPeer) return true;
      if ((m.text||'').includes('@'+currentPeer)) return true;
      return false;
    });
    for (const m of filtered){
      const row = document.createElement('div');
      row.className = 'message ' + (m.self ? 'me' : 'other');
      row.innerHTML = `
        <div class="avatar">${(m.from||'?').slice(0,1)}</div>
        <div>
          <div class="bubble"></div>
          <div class="meta">${m.from} · ${formatTime(m.time)}</div>
        </div>
      `;
      const bubbleEl = row.querySelector('.bubble');
      renderBubbleContent(bubbleEl, m);
      list.appendChild(row);
    }
    list.scrollTop = list.scrollHeight;
  }

  ws.addEventListener('open', ()=>{ appendSystem('已连接到聊天室。'); });
  ws.addEventListener('error', ()=>{ appendSystem('连接出错：无法建立 WebSocket，请检查服务器地址/协议或网络环境'); });

  // 新增：渲染在线用户列表
  function renderOnlineUsers(users){
    if(!onlineListEl) return;
    const arr = Array.isArray(users) ? users : [];
    onlineListEl.innerHTML = '';
    arr.forEach(name => {
      const isMe = name === nickname;
      const item = document.createElement('div');
      item.className = 'contact-item' + (isMe ? ' active me' : '');
      item.setAttribute('role','option');
      if(isMe) item.setAttribute('aria-current','true');
      item.innerHTML = `<div class=\"avatar\">${(name||'?').slice(0,1)}</div><div>${name||'匿名'}${isMe?'<span class=\"me-badge\">我</span>':''}</div>`;
      item.addEventListener('click', ()=>{ msgInput.value += `@${name} `; msgInput.focus(); });
      onlineListEl.appendChild(item);
    });
    if(onlineCountEl) onlineCountEl.textContent = String(arr.length);
  }

  ws.addEventListener('message', (evt)=>{
    let data; try{ data = JSON.parse(evt.data); } catch{ return; }
    if (data.type === 'system'){
      appendSystem(data.text);
    } else if (data.type === 'chat'){
      if ((data.user||'') === nickname) return; // 自己的消息已在发送时记录
      allMessages.push({from: data.user || '匿名', text: data.text || '', time: Date.now(), self: false});
      renderMessages();
    } else if (data.type === 'roster'){
      renderOnlineUsers(data.users || []);
    } else if (data.type === 'music'){
      // 后端广播的音乐卡片
      const d = data.data || {};
      allMessages.push({
        from: data.user || '系统',
        text: '',
        time: Date.now(),
        self: false,
        kind: 'music',
        music: {
          name: d.name || '',
          url: d.url || '',
          singer: d.singer || '',
          image: d.image || ''
        }
      });
      renderMessages();
    } else if (data.type === 'movie'){
      // 后端广播的电影 iframe
      const d = data.data || {};
      allMessages.push({
        from: data.user || '系统',
        text: '',
        time: Date.now(),
        self: false,
        kind: 'movie',
        movie: {
          iframe: d.iframe || '',
          raw: d.raw || ''
        }
      });
      renderMessages();
    } else if (data.type === 'weather'){
      const d = data.data || {};
      allMessages.push({
        from: data.user || '系统',
        text: '',
        time: Date.now(),
        self: false,
        kind: 'weather',
        weather: {
          city: d.city || '',
          cond: d.cond || '',
          temp: d.temp || '',
          high: d.high || '',
          low: d.low || '',
          humidity: d.humidity || '',
          wind: d.wind || '',
          aqi: d.aqi || '',
          tips: d.tips || '',
          update_time: d.update_time || ''
        }
      });
      renderMessages();
    } else if (data.type === 'ai_stream'){
      // 流式 AI 响应：逐字追加
      const id = data.id;
      if (!aiBuffers[id]){
        // 首次收到，新建气泡
        const row = document.createElement('div');
        row.className = 'message other';
        row.innerHTML = `
          <div class="avatar">🤖</div>
          <div>
            <div class="bubble"></div>
            <div class="meta">曼波 · ${formatTime(data.ts)}</div>
          </div>
        `;
        listEl.appendChild(row);
        aiBuffers[id] = row.querySelector('.bubble');
        scrollToBottom();
      }
      if (data.delta){
        aiBuffers[id].textContent += data.delta;
      }
    } else if (data.type === 'ai_stream_end'){
      // 流结束：移除缓存
      delete aiBuffers[data.id];
    } else if (data.type === 'news'){
      const d = data.data || {};
      const items = Array.isArray(d.items) ? d.items : [];
      allMessages.push({
        from: data.user || '系统',
        text: '',
        time: Date.now(),
        self: false,
        kind: 'news',
        news: { source: d.source || '', items }
      });
      renderMessages();
    }
  });

  ws.addEventListener('close', ()=>{ appendSystem('连接已关闭'); });

  function send(){
    const text = msgInput.value.trim();
    if (!text) return;
    if (ws.readyState === WebSocket.OPEN){
      allMessages.push({from: nickname, text, time: Date.now(), self: true});
      renderMessages();
      ws.send(text);
      msgInput.value = '';
    }
  }
  msgInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ e.preventDefault(); send(); } });

  // Emoji 面板：主流表情集合
  const emojiList = [
    '😀','😁','😂','🤣','😊','🙂','😉','😍','😘','😜','🤔','😎','😴','😮','😢','😭','😡','😇','🤗','🤭',
    '👍','👎','🙏','👏','🙌','💪','🤝','👌','✌️','🤙','👀','👋',
    '🎉','💯','🔥','✨','🌟','🌈','⚡','💡','✅','❌','❤️','💖','💔',
    '🎵','🎶','📷','🎁','🏆','🍔','🍕','🍜','🍻','☕','🍵',
    '🐶','🐱','🐭','🐼','🐷','🐸','🐵','🦄','🐤',
    '☀️','🌙','⭐','🌧️','❄️','☁️'
  ];

  function renderEmojiPanel(){
    if(!emojiPanelEl) return;
    emojiPanelEl.innerHTML = '';
    emojiList.forEach(em => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn emoji-btn';
      btn.setAttribute('data-emoji', em);
      btn.setAttribute('role','option');
      btn.textContent = em;
      btn.addEventListener('click', ()=>{ msgInput.value += em; msgInput.focus(); });
      emojiPanelEl.appendChild(btn);
    });
  }

  function toggleEmojiPanel(){
    if(!emojiPanelEl || !emojiToggleBtn) return;
    const opened = !emojiPanelEl.classList.contains('open');
    emojiPanelEl.classList.toggle('open', opened);
    emojiToggleBtn.setAttribute('aria-expanded', opened ? 'true' : 'false');
  }

  if(emojiToggleBtn){
    emojiToggleBtn.addEventListener('click', (e)=>{ e.preventDefault(); e.stopPropagation(); toggleEmojiPanel(); });
  }

  // 点击外部区域关闭面板
  document.addEventListener('click', (e)=>{
    if(!emojiPanelEl || !emojiToggleBtn) return;
    const target = e.target;
    if(emojiPanelEl.classList.contains('open') && !emojiPanelEl.contains(target) && target !== emojiToggleBtn){
      emojiPanelEl.classList.remove('open');
      emojiToggleBtn.setAttribute('aria-expanded','false');
    }
  });
  emojiBtns.forEach(btn=> btn.addEventListener('click', ()=>{ msgInput.value += btn.dataset.emoji; msgInput.focus(); }));

  histBtn.addEventListener('click', ()=>{ appendSystem('历史记录功能正在建设中...'); });

  logoutBtn.addEventListener('click', ()=>{ try{ ws.close(); }catch{} location.href='/'; });

  function initDefaultContacts(){ ['张三','李四','王五','小美','小明'].forEach(n=>contacts.set(n,{name:n})); currentPeer = null; renderContacts(); }

  window.addEventListener('DOMContentLoaded', ()=>{
    renderOnlineUsers([]);
    initDefaultContacts();
    bindAddContactUI();
    renderMessages();
    renderEmojiPanel();
  });
})();
