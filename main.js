import * as checkcode from 'dqi.checkcode_ui';
import { mountDashboard } from './dashboard.js';

// Qollab supplies the selected backend and executes this module on project Run.
const app = mountDashboard({
  info: async () => JSON.parse(String(await checkcode.backend_info.callPromising(backend))),
  execute: async (shots) => JSON.parse(String(await checkcode.live_job.callPromising(backend, shots, 941001))),
});
await app.run();
