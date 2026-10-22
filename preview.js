import { mountDashboard } from './dashboard.js';
const response = await fetch('./index.html');
document.getElementById('preview-root').innerHTML = await response.text();
const app = mountDashboard({
  info: async () => ({name:'Evidence preview',live_supported:false,reason:'This preview displays saved Qiskit evidence. Upload the JavaScript bundle to Qollab and click project Run to execute the live circuit on the selected ideal simulator.'}),
  execute: async () => {throw new Error('No simulator attached to this evidence preview.');},
});
await app.run();
document.getElementById('top-status').textContent='Evidence preview';
