const ganttDiv = document.getElementById('gantt');

function drawGantt(data) {
  const sats = data.satellites;
  if (!sats.length) {
    ganttDiv.innerHTML = `
      <div style="color:#555577; padding:20px; font-size:12px;">
        No maneuvers scheduled yet.<br>
        Use POST /api/maneuver/schedule to add burns.
      </div>`;
    return;
  }

  let html = `<div style="padding:10px; font-size:11px;">`;
  sats.forEach(sat => {
    const color = sat.status === 'NOMINAL'  ? '#00ff88'
                : sat.status === 'EVADING'  ? '#ffaa00'
                : sat.status === 'EOL'      ? '#ff4444' : '#888888';
    html += `
      <div style="margin-bottom:10px;">
        <div style="color:${color}; font-weight:bold; margin-bottom:4px;">
          ${sat.id}
          <span style="color:#555577; font-weight:normal; margin-left:8px;">
            ${sat.status}
          </span>
        </div>
        <div style="background:#1a1a3a; border-radius:3px; height:20px;
                    position:relative; width:100%;">
          <div style="background:${color}; height:100%; border-radius:3px;
                      width:${(sat.fuel_kg/50)*100}%; opacity:0.7;">
          </div>
          <span style="position:absolute; right:6px; top:3px;
                       color:#ffffff; font-size:10px;">
            Fuel: ${sat.fuel_kg.toFixed(1)}kg
          </span>
        </div>
      </div>`;
  });
  html += `
    <div style="color:#555577; margin-top:10px; font-size:10px;">
      ${data.timestamp}
    </div>
  </div>`;
  ganttDiv.innerHTML = html;
}

window.addEventListener('snapshotUpdate', e => drawGantt(e.detail));