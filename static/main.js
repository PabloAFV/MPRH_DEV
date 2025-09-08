(() => {
  const $ = (id) => document.getElementById(id);
  const safeNum = (v, d = 0) => (typeof v === 'number' && !isNaN(v) ? v : d);
  const asIntOrNull = (v) => (typeof v === 'number' && !isNaN(v) ? Math.round(v) : null);

  // Elementos
  const modeIndicator   = $('mode-indicator');
  const tempValue       = $('temp-value');
  const flowValue       = $('flow-value');
  const pressure1Value  = $('pressure1-value');
  const pressure2Value  = $('pressure2-value');
  const resKidneySpan   = $('res-kidney');
  const resistanceValue = $('resistance-value');
  const bubbleState     = $('bubble-state');
  const pumpState       = $('pump-state');
  const btnPump         = $('toggle-pump');
  const btnMode         = $('mode-switch');
  const btnEstop        = $('emergency-stop');
  const btnCooling      = $('toggle-cooling');

  const tabK1 = $('tab-k1');
  const tabK2 = $('tab-k2');
  const chartKidneySpan = $('chart-kidney');

  // Badge de conexión
  let connBadge = document.getElementById('conn-badge');
  if (!connBadge) {
    connBadge = document.createElement('span');
    connBadge.id = 'conn-badge';
    connBadge.className = 'badge disconnected';
    connBadge.textContent = 'Desconectado';
    document.querySelector('.right-head').appendChild(connBadge);
  }

  // Estado de pestaña activa
  let activeKidney = 1;
  function setActiveKidney(k) {
    activeKidney = (k === 2) ? 2 : 1;
    chartKidneySpan.textContent = String(activeKidney);
    resKidneySpan.textContent   = String(activeKidney);
    tabK1.classList.toggle('active', activeKidney === 1);
    tabK2.classList.toggle('active', activeKidney === 2);

    // Mostrar solo las tarjetas de presión del riñón activo
    document.querySelectorAll('.kidney-only').forEach(el => {
      const targetKidney = parseInt(el.dataset.kidney);
      el.style.display = (targetKidney === activeKidney) ? '' : 'none';
    });
  }
  tabK1.addEventListener('click', () => setActiveKidney(1));
  tabK2.addEventListener('click', () => setActiveKidney(2));

  // Gráficas
  const maxPoints = 50;
  const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim();
  const dangerColor  = getComputedStyle(document.documentElement).getPropertyValue('--danger').trim();

  const tempCtx     = document.getElementById('temp-chart').getContext('2d');
  const flowCtx     = document.getElementById('flow-chart').getContext('2d');
  const pressureCtx = document.getElementById('pressure-chart').getContext('2d');

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

  const pressureChart = new Chart(pressureCtx, {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'mmHg', data: [], borderColor: primaryColor, backgroundColor: primaryColor, fill: false, pointRadius: 0, tension: 0.2 }] },
    options: { responsive: true, animation: false, maintainAspectRatio: false,
      scales: { x:{title:{display:true,text:'Tiempo (s)'}}, y:{title:{display:true,text:'Presión (mmHg)'}} } }
  });

  let t = 0;
  function addPoint(chart, v) {
    chart.data.labels.push(t);
    chart.data.datasets[0].data.push(v);
    if (chart.data.labels.length > maxPoints) {
      chart.data.labels.shift();
      chart.data.datasets[0].data.shift();
    }
    chart.update('none');
  }

  function setConnectedBadge(connected) {
    if (connected) {
      connBadge.textContent = 'Conectado';
      connBadge.classList.add('connected');
      connBadge.classList.remove('disconnected');
    } else {
      connBadge.textContent = 'Desconectado';
      connBadge.classList.add('disconnected');
      connBadge.classList.remove('connected');
    }
  }

  function setTempIndicator(temp) {
    if (temp >= 4.0 && temp <= 8.0) {
      tempValue.classList.add('ok'); tempValue.classList.remove('warn');
    } else {
      tempValue.classList.add('warn'); tempValue.classList.remove('ok');
    }
  }

  // Últimos valores para cálculo de resistencia según pestaña
  let lastP1 = null, lastP2 = null, lastFlowMlMin = 0;

  function computeResistanceMmHgMinPerL(selKidney) {
    const qLmin = lastFlowMlMin / 1000.0;
    const p = (selKidney === 2 ? lastP2 : lastP1);
    if (p == null || !isFinite(p) || qLmin <= 0) return null;
    return p / qLmin;
  }

  async function fetchAndUpdate() {
    try {
      const res = await fetch('/api/status', { cache: 'no-cache' });
      const s = await res.json();

      // Conexión
      const connected = (typeof s.connected === 'boolean') ? s.connected : true;
      setConnectedBadge(connected);

      // Valores básicos
      const temp      = safeNum(s.temperature, 0);
      const flow      = safeNum(s.flow, 0);
      const press     = asIntOrNull(s.pressure);
      const p1        = asIntOrNull(s.pressure1 != null ? s.pressure1 : press);
      const p2        = asIntOrNull(s.pressure2 != null ? s.pressure2 : null);
      const bubble    = !!s.bubble;
      const pumpOn    = !!s.pumpOn;
      const mode      = s.mode || 'Manual';
      const coolingOn = !!s.coolingOn;

      // Cache
      lastFlowMlMin = flow;
      lastP1 = p1;
      lastP2 = (p2 != null) ? p2 : null;

      // UI
      tempValue.textContent      = `${temp.toFixed(1)} °C`;
      flowValue.textContent      = `${flow} ml/min`;
      if (p1 != null) pressure1Value.textContent = `${p1} mmHg`;
      if (p2 != null) pressure2Value.textContent = `${p2} mmHg`;
      bubbleState.textContent    = bubble ? 'Sí' : 'No';
      pumpState.textContent      = pumpOn ? 'ON' : 'OFF';
      modeIndicator.textContent  = `Modo: ${mode}`;
      setTempIndicator(temp);

      // Resistencia del riñón activo
      const R = computeResistanceMmHgMinPerL(activeKidney);
      resistanceValue.textContent = (R != null) ? `${R.toFixed(1)} mmHg·min/L` : '--';

      // Botones
      const manual = (mode === 'Manual');
      btnCooling.style.display = manual ? 'inline-block' : 'none';
      btnCooling.textContent   = coolingOn ? 'Desactivar refrigeración' : 'Activar refrigeración';
      btnPump.disabled         = !manual;
      btnEstop.disabled        = !manual;

      // Series
      addPoint(tempChart, temp);
      addPoint(flowChart, flow);

      // Presión del riñón activo a la gráfica
      const pSel = (activeKidney === 2) ? (p2 != null ? p2 : null) : (p1 != null ? p1 : null);
      if (pSel != null) addPoint(pressureChart, pSel);
      else addPoint(pressureChart, NaN);

      t += 2;
    } catch (e) {
      console.error('fetch /api/status failed', e);
      setConnectedBadge(false);
    }
  }

  // Controles
  btnPump.addEventListener('click', async () => {
    try {
      const st = await (await fetch('/api/status', { cache: 'no-cache' })).json();
      await fetch('/api/pump', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pumpOn: !st.pumpOn })
      });
    } catch (e) { console.error(e); }
  });

  btnMode.addEventListener('click', async () => {
    try {
      const st = await (await fetch('/api/status', { cache: 'no-cache' })).json();
      const next = (st.mode === 'Automático') ? 'Manual' : 'Automático';
      await fetch('/api/mode', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: next })
      });
    } catch (e) { console.error(e); }
  });

  btnEstop.addEventListener('click', async () => {
    try { await fetch('/api/emergency-stop', { method: 'POST' }); }
    catch (e) { console.error(e); }
  });

  $('toggle-cooling').addEventListener('click', async () => {
    try {
      const st = await (await fetch('/api/status', { cache: 'no-cache' })).json();
      await fetch('/api/cooling', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coolingOn: !st.coolingOn })
      });
    } catch (e) { console.error(e); }
  });

  // Init
  setActiveKidney(1);
  fetchAndUpdate();
  setInterval(fetchAndUpdate, 2000);
})();
