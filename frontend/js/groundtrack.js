// frontend/js/groundtrack.js
const mapImg = new Image();
mapImg.crossOrigin = "anonymous";
mapImg.src = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1280px-Equirectangular_projection_SW.jpg';

const gt = document.getElementById('groundtrack');
const ctx = gt.getContext('2d');

let W, H;

function resizeCanvas() {
  W = gt.parentElement.clientWidth;
  H = gt.parentElement.clientHeight - 30;
  gt.width = W;
  gt.height = H;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

const satTrails = {};

function latLonToXY(lat, lon) {
  const x = (lon + 180) / 360 * W;
  const y = (90 - lat) / 180 * H;
  return [x, y];
}

function drawGroundTrack(data) {
  resizeCanvas();
  ctx.clearRect(0, 0, W, H);

  // ── World map background ──────────────────────────────────
  if (mapImg.complete && mapImg.naturalWidth > 0) {
    ctx.drawImage(mapImg, 0, 0, W, H);
    // Darken slightly so dots are visible
    ctx.fillStyle = 'rgba(0, 0, 20, 0.45)';
    ctx.fillRect(0, 0, W, H);
  } else {
    ctx.fillStyle = '#0a0a2a';
    ctx.fillRect(0, 0, W, H);
    // Draw grid lines as fallback
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 0.5;
    for (let lon = -180; lon <= 180; lon += 30) {
      const [x] = latLonToXY(0, lon);
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let lat = -90; lat <= 90; lat += 30) {
      const [, y] = latLonToXY(lat, 0);
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
  }
  
  // ── Terminator (day/night boundary) ──────────────────────
  function getSunLatLon() {
    const d = (Date.now() - Date.UTC(2000,0,1,12)) / 86400000;
    const L = (280.46 + 0.9856474 * d) % 360;
    const g = (357.528 + 0.9856003 * d) % 360;
    const lam = L + 1.915*Math.sin(g*Math.PI/180) + 0.02*Math.sin(2*g*Math.PI/180);
    const eps = 23.439 - 0.0000004 * d;
    const sinDec = Math.sin(eps*Math.PI/180) * Math.sin(lam*Math.PI/180);
    const dec = Math.asin(sinDec) * 180/Math.PI;
    const ra = Math.atan2(Math.cos(eps*Math.PI/180)*Math.sin(lam*Math.PI/180),
                          Math.cos(lam*Math.PI/180)) * 180/Math.PI;
    const lon = ra - (280.46061837 + 360.98564736629*d) % 360;
    return { lat: dec, lon: ((lon+180)%360)-180 };
  }

  const sun = getSunLatLon();
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,30,0.45)';
  ctx.beginPath();
  let firstT = true;
  for (let ix = 0; ix <= W; ix += 3) {
    const lon = (ix / W) * 360 - 180;
    const termLat = Math.atan2(
      -Math.cos((lon - sun.lon) * Math.PI/180),
      Math.tan(sun.lat * Math.PI/180)
    ) * 180/Math.PI;
    const [tx, ty] = latLonToXY(termLat, lon);
    if (firstT) { ctx.moveTo(tx, ty); firstT = false; }
    else ctx.lineTo(tx, ty);
  }
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fill();
  ctx.restore();

  // ── Equator and prime meridian ────────────────────────────
  ctx.strokeStyle = 'rgba(255,255,255,0.15)';
  ctx.lineWidth = 0.8;
  const [, eqY] = latLonToXY(0, 0);
  ctx.beginPath(); ctx.moveTo(0, eqY); ctx.lineTo(W, eqY); ctx.stroke();
  const [pmX] = latLonToXY(0, 0);
  ctx.beginPath(); ctx.moveTo(pmX, 0); ctx.lineTo(pmX, H); ctx.stroke();

  // ── Debris dots ───────────────────────────────────────────
  ctx.fillStyle = 'rgba(255, 100, 100, 0.5)';
  data.debris_cloud.forEach(([id, lat, lon, alt]) => {
    const [x, y] = latLonToXY(lat, lon);
    ctx.beginPath();
    ctx.arc(x, y, 1.5, 0, Math.PI * 2);
    ctx.fill();
  });

  // ── Satellite trails + dots ───────────────────────────────
  data.satellites.forEach(sat => {
    if (!satTrails[sat.id]) satTrails[sat.id] = [];
    satTrails[sat.id].push({ lat: sat.lat, lon: sat.lon, t: Date.now() });
    const cutoff = Date.now() - 90 * 60 * 1000;
    satTrails[sat.id] = satTrails[sat.id].filter(p => p.t > cutoff);

    const color = sat.status === 'NOMINAL'  ? '#00ff88'
                : sat.status === 'EVADING'  ? '#ffaa00'
                : sat.status === 'EOL'      ? '#ff4444'
                : '#888888';

    // Trail
    const trail = satTrails[sat.id];
    if (trail.length > 1) {
      for (let i = 1; i < trail.length; i++) {
        const alpha = (i / trail.length) * 0.4;
        ctx.strokeStyle = `rgba(100,200,255,${alpha})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        const [x1, y1] = latLonToXY(trail[i-1].lat, trail[i-1].lon);
        const [x2, y2] = latLonToXY(trail[i].lat, trail[i].lon);
        // Skip if trail wraps around date line
        if (Math.abs(trail[i].lon - trail[i-1].lon) < 90) {
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
        }
      }
    }
    // Predicted trajectory (dashed, next 90 min)
    ctx.save();
    ctx.setLineDash([4, 6]);
    ctx.strokeStyle = 'rgba(100,200,255,0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    const STEPS = 60;
    for (let s = 0; s <= STEPS; s++) {
      const dt = s * (90 * 60 / STEPS); // seconds ahead
      // LEO: ~360deg / 5400s orbital period ≈ 0.0667 deg/s longitude
      const futureLon = ((sat.lon + 0.0667 * dt) + 180) % 360 - 180;
      const futureLat = sat.lat * Math.cos((s / STEPS) * Math.PI * 2); // sinusoidal approx
      const [px, py] = latLonToXY(futureLat, futureLon);
      s === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.restore();

    // Dot with glow effect
    const [x, y] = latLonToXY(sat.lat, sat.lon);

    // Glow
    const grd = ctx.createRadialGradient(x, y, 0, x, y, 10);
    grd.addColorStop(0, color + 'aa');
    grd.addColorStop(1, 'transparent');
    ctx.fillStyle = grd;
    ctx.beginPath();
    ctx.arc(x, y, 10, 0, Math.PI * 2);
    ctx.fill();

    // Solid dot
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();

    // White border
    ctx.strokeStyle = 'rgba(255,255,255,0.6)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Label
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 9px Arial';
    ctx.shadowColor = '#000000';
    ctx.shadowBlur = 3;
    ctx.fillText(sat.id, x + 7, y - 4);
    ctx.shadowBlur = 0;
  });

  // ── Ground stations ───────────────────────────────────────
  const groundStations = [
    { name: 'ISTRAC', lat: 13.03, lon: 77.52 },
    { name: 'Svalbard', lat: 78.23, lon: 15.41 },
    { name: 'Goldstone', lat: 35.43, lon: -116.89 },
    { name: 'IIT Delhi', lat: 28.54, lon: 77.19 },
    { name: 'McMurdo', lat: -77.85, lon: 166.67 },
    { name: 'Punta Arenas', lat: -53.15, lon: -70.92 },
  ];
  groundStations.forEach(gs => {
    const [gx, gy] = latLonToXY(gs.lat, gs.lon);
    ctx.fillStyle = '#00ccff';
    ctx.beginPath();
    ctx.arc(gx, gy, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = '#00ccff';
    ctx.font = '8px Arial';
    ctx.fillText(gs.name, gx + 5, gy + 3);
  });

  // ── Stats overlay ─────────────────────────────────────────
  ctx.fillStyle = 'rgba(0,0,0,0.5)';
  ctx.fillRect(5, H - 40, 220, 35);
  ctx.fillStyle = '#00ff88';
  ctx.font = '10px Arial';
  ctx.fillText(`Satellites: ${data.satellites.length}`, 10, H - 24);
  ctx.fillStyle = '#ff6464';
  ctx.fillText(`Debris: ${data.debris_cloud.length}`, 10, H - 10);
  ctx.fillStyle = '#ffffff';
  ctx.fillText(data.timestamp?.slice(0, 19) || '', 90, H - 10);
}

// Load map then wait for data
mapImg.onload = () => console.log('World map loaded!');
mapImg.onerror = () => console.warn('Map failed to load, using grid fallback');

window.addEventListener('snapshotUpdate', e => drawGroundTrack(e.detail));
