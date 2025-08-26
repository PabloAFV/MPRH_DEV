(() => {
  const $ = (id) => document.getElementById(id);
  const safeNum = (v, d = 0) => (typeof v === 'number' && !isNaN(v) ? v : d);

  const modeIndicator = $('mode-indicator');
  const tempValue = $('temp-value');
  const flowValue = $('flow-value');
  const pressureValue = $('pressure-value');
  const bubbleState = $('bubble-state');
  const resistanceValue = $('resistance-value');
  const pumpState = $('pump-state');
  const btnPump = $('toggle-pump');
  const btnMode = $('mode-switch');
  const btnEstop = $('emergency-stop');
  const btnCooling = $('toggle-cooling');

  let connBadge = document.getElementById('conn-badge');
  if (!connBadge) {
    connBadge = document.createElement('span');
    connBadge.id = 'conn-badge';
    connBadge.className = 'badge disconnected';
    connBadge.textContent = 'Desconectado';
    document.querySelector('.header-bar').appendChild(connBadge);
  }

  const maxPoints = 50;
  const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim();
  const dangerColor = getComputedStyle(document.documentElement).getPropertyValue('--danger').trim();

  const tempCtx = document.getElementById('temp-chart').getContext('2d');
  const flowCtx = document.getElementById('flow-chart').getContext('2d');

  const tempChart = new Chart(tempCtx, {
    type: 'line',
    data: { labels: [], datasets: [{ label: '°C', data: [], borderColor: primaryColor, backgroundColor: primaryColor, fill: false, pointRadius: 0, tension: 0.2 }] },
    options: { responsive: true, animation: false, maintainAspectRatio: false,
      scales: { x:{title:{display:true,text:'Tiempo (s)'}}, y:{title:{display:true,text:'Temperatura (°C)'}} } }
  });

  const flowChart = new Chart(flowCtx, {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'ml/min', data: [], borderColor: dangerColor, backgroundColor: dangerColor, fill: false, pointRadius: 0, tension: 0.2 }] },
    options: { responsive: true, animation: false, maintainAspectRatio: false,
      scales: { x:{title:{display:true,text:'Tiempo (s)'}}, y:{title:{display:true,text:'Caudal (ml/min)'}, beginAtZero:true} } }
  });

  let t = 0;
  function addPoint(chart, v){ chart.data.labels.push(t); chart.data.datasets[0].data.push(v);
    if(chart.data.labels.length>maxPoints){ chart.data.labels.shift(); chart.data.datasets[0].data.shift(); }
    chart.update('none'); }

  function setConnectedBadge(connected){
    if (connected){ connBadge.textContent='Conectado'; connBadge.classList.add('connected'); connBadge.classList.remove('disconnected'); }
    else { connBadge.textContent='Desconectado'; connBadge.classList.add('disconnected'); connBadge.classList.remove('connected'); }
  }

  function setTempIndicator(temp){
    if (temp>=4.0 && temp<=8.0){ tempValue.classList.add('ok'); tempValue.classList.remove('warn'); }
    else { tempValue.classList.add('warn'); tempValue.classList.remove('ok'); }
  }

  async function fetchAndUpdate(){
    try{
      const res = await fetch('/api/status', { cache: 'no-cache' });
      const s = await res.json();
      console.log('status:', s); // <-- LOG para depurar

      const connected = (typeof s.connected==='boolean') ? s.connected : true;
      setConnectedBadge(connected);

      const temp = safeNum(s.temperature, 0);
      const flow = safeNum(s.flow, 0);
      const press = safeNum(s.pressure, 0);
      const bubble = !!s.bubble;
      const pumpOn = !!s.pumpOn;
      const mode = s.mode || 'Manual';
      const coolingOn = !!s.coolingOn;

      tempValue.textContent = `${temp.toFixed(1)} °C`;
      flowValue.textContent = `${flow} ml/min`;
      pressureValue.textContent = `${press} mmHg`;
      bubbleState.textContent = bubble ? 'Sí' : 'No';
      pumpState.textContent = pumpOn ? 'ON' : 'OFF';
      modeIndicator.textContent = `Modo: ${mode}`;
      setTempIndicator(temp);

      const qLmin = flow / 1000.0;
      resistanceValue.textContent = qLmin>0 ? `${(press/qLmin).toFixed(1)} mmHg·min/L` : '--';

      // En automático: deshabilita cambios. Si desconectado, NO bloqueamos para pruebas.
      const manual = (mode === 'Manual');
      btnCooling.style.display = manual ? 'inline-block' : 'none';
      btnCooling.textContent = coolingOn ? 'Desactivar refrigeración' : 'Activar refrigeración';
      btnPump.disabled = !manual;
      btnEstop.disabled = !manual;

      addPoint(tempChart, temp);
      addPoint(flowChart, flow);
      t += 2;
    }catch(e){
      console.error('fetch /api/status failed', e);
      setConnectedBadge(false);
    }
  }

  btnPump.addEventListener('click', async () => {
    try{
      const st = await (await fetch('/api/status', { cache: 'no-cache' })).json();
      await fetch('/api/pump', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ pumpOn: !st.pumpOn }) });
    }catch(e){ console.error(e); }
  });

  btnMode.addEventListener('click', async () => {
    try{
      const st = await (await fetch('/api/status', { cache: 'no-cache' })).json();
      const next = (st.mode === 'Automático') ? 'Manual' : 'Automático';
      await fetch('/api/mode', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ mode: next }) });
    }catch(e){ console.error(e); }
  });

  btnEstop.addEventListener('click', async () => {
    try{ await fetch('/api/emergency-stop', { method:'POST' }); }catch(e){ console.error(e); }
  });

  document.getElementById('toggle-cooling').addEventListener('click', async () => {
    try{
      const st = await (await fetch('/api/status', { cache: 'no-cache' })).json();
      await fetch('/api/cooling', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ coolingOn: !st.coolingOn }) });
    }catch(e){ console.error(e); }
  });

  fetchAndUpdate();
  setInterval(fetchAndUpdate, 2000);
})();
