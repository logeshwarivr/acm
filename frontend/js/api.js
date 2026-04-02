const API_BASE = 'http://localhost:8000/api';
let snapshotData = null;

async function fetchSnapshot() {
  try {
    const res = await fetch(`${API_BASE}/visualization/snapshot`);
    snapshotData = await res.json();
    // Notify all modules
    window.dispatchEvent(
      new CustomEvent('snapshotUpdate', { detail: snapshotData }));
  } catch(e) { console.error('Snapshot fetch failed:', e); }
}

// Poll every 1 second for real-time feel
setInterval(fetchSnapshot, 1000);
fetchSnapshot();
