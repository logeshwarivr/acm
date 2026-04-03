const heatCanvas = document.getElementById('heatmap');
const hctx = heatCanvas.getContext('2d');

function drawHeatmap(data) {
  const W = heatCanvas.parentElement.clientWidth;
  const H = heatCanvas.parentElement.clientHeight - 30;
  heatCanvas.width = W; heatCanvas.height = H;
  hctx.clearRect(0, 0, W, H);

  const sats = data.satellites;
  if (!sats.length) return;

  const barW = Math.min(50, (W - 40) / sats.length - 10);
  const maxH = Math.min(H - 60, 120);

  sats.forEach((sat, i) => {
    const fuelPct = sat.fuel_kg / 50.0;
    const barH = maxH * fuelPct;
    const x = 30 + i * (barW + 10);
    const y = H - 40 - barH;

    // Bar color: green > yellow > red
    const color = fuelPct > 0.5 ? '#00ff88'
                : fuelPct > 0.2 ? '#ffaa00' : '#ff4444';

    // Background bar
    hctx.fillStyle = '#1a1a3a';
    hctx.fillRect(x, H - 40 - maxH, barW, maxH);

    // Fuel bar
    hctx.fillStyle = color;
    hctx.fillRect(x, y, barW, barH);

    // Label
    hctx.fillStyle = '#ffffff';
    hctx.font = '10px Arial';
    hctx.fillText(sat.id.replace('SAT-','S'), x + 2, H - 25);
    hctx.fillText(Math.round(fuelPct * 100) + '%', x + 2, H - 12);
  });

  // Title
  hctx.fillStyle = '#7ec8e3';
  hctx.font = '11px Arial';
  hctx.fillText('FUEL LEVEL PER SATELLITE', 10, 16);
}

window.addEventListener('snapshotUpdate', e => drawHeatmap(e.detail));
