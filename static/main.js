(async () => {
  const maxPoints = 50;
  const tempCtx = document.getElementById('temp-chart').getContext('2d');
  const flowCtx = document.getElementById('flow-chart').getContext('2d');
  const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim();
  const dangerColor = getComputedStyle(document.documentElement).getPropertyValue('--danger').trim();

  const tempChart = new Chart(tempCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: '°C',
        data: [],
        borderColor: primaryColor,
        backgroundColor: primaryColor,
        fill: false,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: { display: true, title: { display: true, text: "Tiempo" } },
        y: { display: true, title: { display: true, text: "Temperatura (°C)" }, beginAtZero: true }
      }
    }
  });

  const flowChart = new Chart(flowCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'ml/min',
        data: [],
        borderColor: dangerColor,
        backgroundColor: dangerColor,
        fill: false,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: { display: true, title: { display: true, text: "Tiempo" } },
        y: { display: true, title: { display: true, text: "Caudal (ml/min)" }, beginAtZero: true }
      }
    }
  });

  let time = 0;

  async function fetchAndUpdate() {
    try {
      const res = await fetch('/api/status');
      const s = await res.json();

      // Actualiza valores
      document.getElementById('temp-value').textContent = `${s.temperature.toFixed(1)} °C`;
      document.getElementById('flow-value').textContent = `${s.flow} ml/min`;
      document.getElementById('pressure-value').textContent = `${s.pressure} mmHg`;
      document.getElementById('bubble-state').textContent = s.bubble ? 'Sí' : 'No';
      const qLmin = s.flow / 1000;
      document.getElementById('resistance-value').textContent =
        qLmin > 0 ? `${(s.pressure / qLmin).toFixed(1)} mmHg·min/L` : '--';
      document.getElementById('pump-state').textContent = s.pumpOn ? 'ON' : 'OFF';
      document.getElementById('mode-indicator').textContent = `Modo: ${s.mode}`;

      // Botones: solo manual permite control
      document.getElementById('toggle-pump').disabled = s.mode === 'Automático';
      document.getElementById('emergency-stop').disabled = s.mode === 'Automático';

      // Refrigeración solo en modo manual
      const toggleCooling = document.getElementById('toggle-cooling');
      if (s.mode === 'Manual') {
        toggleCooling.style.display = 'inline-block';
        toggleCooling.textContent = s.coolingOn ? 'Desactivar refrigeración' : 'Activar refrigeración';
        toggleCooling.disabled = false;
      } else {
        toggleCooling.style.display = 'none';
      }

      // Temperatura óptima (verde), fuera de rango (rojo)
      const tempValue = document.getElementById('temp-value');
      if (s.temperature >= 4.0 && s.temperature <= 8.0) {
        tempValue.classList.add('ok');
        tempValue.classList.remove('warn');
      } else {
        tempValue.classList.add('warn');
        tempValue.classList.remove('ok');
      }

      // Graficar
      tempChart.data.labels.push(time);
      tempChart.data.datasets[0].data.push(s.temperature);
      if (tempChart.data.labels.length > maxPoints) {
        tempChart.data.labels.shift();
        tempChart.data.datasets[0].data.shift();
      }
      tempChart.update();

      flowChart.data.labels.push(time);
      flowChart.data.datasets[0].data.push(s.flow);
      if (flowChart.data.labels.length > maxPoints) {
        flowChart.data.labels.shift();
        flowChart.data.datasets[0].data.shift();
      }
      flowChart.update();

      time += 1;
    } catch (e) {
      console.error(e);
    }
  }

  document.getElementById('toggle-pump').addEventListener('click', async () => {
    try {
      const current = (await (await fetch('/api/status')).json()).pumpOn;
      await fetch('/api/pump', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pumpOn: !current })
      });
    } catch (e) {
      console.error(e);
    }
  });

  document.getElementById('mode-switch').addEventListener('click', async () => {
    try {
      const current = (await (await fetch('/api/status')).json()).mode;
      const next = current === 'Automático' ? 'Manual' : 'Automático';
      await fetch('/api/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: next })
      });
    } catch (e) {
      console.error(e);
    }
  });

  document.getElementById('emergency-stop').addEventListener('click', async () => {
    try {
      await fetch('/api/emergency-stop', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  });

  // Nuevo: Refrigeración
  document.getElementById('toggle-cooling').addEventListener('click', async () => {
    try {
      const current = (await (await fetch('/api/status')).json()).coolingOn;
      await fetch('/api/cooling', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coolingOn: !current })
      });
    } catch (e) {
      console.error(e);
    }
  });

  fetchAndUpdate();
  setInterval(fetchAndUpdate, 2000);
})();
