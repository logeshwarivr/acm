const scheduledManeuvers = []; // populated when maneuvers are POSTed

// Intercept maneuver POSTs from console for demo — 
// in production your backend should return these in snapshot
window.addManeuver = function(satId, burns) {
  burns.forEach(b => scheduledManeuvers.push({ satId, ...b }));
};
const ganttDiv = document.getElementById('gantt');

function drawGantt(data) {
  const sats = data.satellites;
  if (!sats.length) {
    ganttDiv.innerHTML = `<div style="color:#555577;padding:20px;font-size:12px;">
      No satellites in snapshot.</div>`;
    return;
  }

  const now = new Date(data.timestamp);
  const windowMs = 4 * 60 * 60 * 1000; // show 4-hour window

  let html = `<div style="padding:10px;font-size:11px;overflow-y:auto;max-height:calc(100% - 30px);">`;

  sats.forEach(sat => {
    const color = sat.status === 'NOMINAL' ? '#00ff88'
                : sat.status === 'EVADING' ? '#ffaa00'
                : sat.status === 'EOL'     ? '#ff4444' : '#888888';

    const burns = scheduledManeuvers.filter(m => m.satId === sat.id);

    html += `
      <div style="margin-bottom:14px;">
        <div style="color:${color};font-weight:bold;margin-bottom:4px;">
          ${sat.id}
          <span style="color:#555577;font-weight:normal;margin-left:8px;">${sat.status}</span>
          <span style="color:#7ec8e3;margin-left:8px;">Fuel: ${sat.fuel_kg.toFixed(1)}kg</span>
        </div>
        <div style="background:#1a1a3a;border-radius:3px;height:24px;position:relative;width:calc(100% - 10px);">`;

    burns.forEach(burn => {
      const burnStart = new Date(burn.burnTime);
      const offsetMs = burnStart - now;
      if (offsetMs < 0 || offsetMs > windowMs) return;
      const leftPct = (offsetMs / windowMs) * 100;
      const widthPct = 3; // burn block width
      const cooldownPct = (600000 / windowMs) * 100; // 600s cooldown

      html += `
          <div title="${burn.burn_id}" style="position:absolute;left:${leftPct.toFixed(1)}%;
               top:2px;height:20px;width:${widthPct}%;background:#ffaa00;
               border-radius:2px;font-size:9px;line-height:20px;
               padding-left:3px;color:#000;overflow:hidden;white-space:nowrap;">
            ${burn.burn_id}
          </div>
          <div title="Cooldown 600s" style="position:absolute;
               left:${(leftPct+widthPct).toFixed(1)}%;top:2px;
               height:20px;width:${cooldownPct.toFixed(1)}%;
               background:rgba(255,100,100,0.25);border-radius:2px;">
          </div>`;
    });

    // Now marker
    html += `
          <div style="position:absolute;left:0;top:0;height:100%;
               width:2px;background:#00ff88;opacity:0.6;"></div>
        </div>
        ${burns.length === 0 ? '<div style="color:#333355;font-size:10px;margin-top:2px;">No burns scheduled</div>' : ''}
      </div>`;
  });

  html += `<div style="color:#555577;margin-top:8px;font-size:10px;">${data.timestamp}</div></div>`;
  ganttDiv.innerHTML = html;
}

window.addEventListener('snapshotUpdate', e => drawGantt(e.detail));
