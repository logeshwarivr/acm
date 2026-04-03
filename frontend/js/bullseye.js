const bCanvas = document.getElementById('bullseye');
const bctx = bCanvas.getContext('2d');

function drawBullseye(data) {
  const W = bCanvas.parentElement.clientWidth;
  const H = bCanvas.parentElement.clientHeight - 30;
  bCanvas.width = W; bCanvas.height = H;
  bctx.clearRect(0, 0, W, H);

  const cx = W / 2, cy = H / 2;
  const maxR = Math.min(cx, cy) - 20;

  // Draw rings
  [1, 0.6, 0.3].forEach((r, i) => {
    const colors = ['#1a3a1a','#3a3a1a','#3a1a1a'];
    bctx.beginPath();
    bctx.arc(cx, cy, maxR * r, 0, Math.PI * 2);
    bctx.strokeStyle = colors[i];
    bctx.lineWidth = 1;
    bctx.stroke();
  });

  // Ring labels
  bctx.fillStyle = '#555577';
  bctx.font = '9px Arial';
  bctx.fillText('5km', cx + maxR * 0.6 + 2, cy);
  bctx.fillText('1km', cx + maxR * 0.3 + 2, cy);

  // Center crosshair
  bctx.strokeStyle = '#00ff88';
  bctx.lineWidth = 1;
  bctx.beginPath();
  bctx.moveTo(cx - 8, cy); bctx.lineTo(cx + 8, cy);
  bctx.moveTo(cx, cy - 8); bctx.lineTo(cx, cy + 8);
  bctx.stroke();

  // Plot debris relative to first satellite
  if (data.satellites.length && data.debris_cloud.length) {
    const sat = data.satellites[0];
    data.debris_cloud.forEach(([id, dlat, dlon, dalt]) => {
      const dLat = dlat - sat.lat;
      const dLon = dlon - sat.lon;
      const dist = Math.sqrt(dLat * dLat + dLon * dLon);
      const distKm = dist * 111;

      if (distKm > 50) return; // only show nearby debris

      const angle = Math.atan2(dLon, dLat);
      const plotR = Math.min((distKm / 50) * maxR, maxR);
      const px = cx + plotR * Math.sin(angle);
      const py = cy - plotR * Math.cos(angle);

      const color = distKm < 0.1 ? '#ff4444'
                  : distKm < 1   ? '#ff4444'
                  : distKm < 5   ? '#ffaa00' : '#00aa44';

      bctx.beginPath();
      bctx.arc(px, py, 3, 0, Math.PI * 2);
      bctx.fillStyle = color;
      bctx.fill();
    });
  }

  // Legend
  bctx.font = '9px Arial';
  [['#ff4444','< 1km CRITICAL'],['#ffaa00','< 5km WARNING'],
   ['#00aa44','SAFE']].forEach(([c, l], i) => {
    bctx.fillStyle = c;
    bctx.fillRect(8, H - 50 + i * 14, 8, 8);
    bctx.fillStyle = '#aaaaaa';
    bctx.fillText(l, 20, H - 43 + i * 14);
  });

  // Center satellite label
  bctx.fillStyle = '#00ff88';
  bctx.font = '10px Arial';
  const label = data.satellites[0]?.id || 'No Satellite';
  bctx.fillText(label, cx - 20, cy + 16);
}

window.addEventListener('snapshotUpdate', e => drawBullseye(e.detail));
