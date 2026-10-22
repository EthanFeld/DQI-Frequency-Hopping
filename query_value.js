import { CHECKCODE_RESULTS as measured } from './data/checkcode_results.js';

// Transfer calculations. Compact upload and original audit contain identical measured evidence.
export const QUERY_VALUE_MODEL = {
  schema_version: 1,
  kind: 'commercial_scenario_and_analytic_projection',
  application: 'Industrial telemetry frequency planning with on-demand availability access',
  measured_evidence_sha256: 'cf743dff61214a7cd4dd1099eecb7cc57f22cc25185d184bf5c73dd9bf70686d',
  audited_evidence_sha256: 'ce75aa183dbefb1288da97a8852f6bc716e1501f3e1adefa4eb9efd7461f175e',
  measured_evidence: './data/checkcode_results.json',
  defaults: { sensors: 10000, reportsPerHour: 480, airtimeMs: 10,
    costPerMillionAttempts: 10, incrementalCostPerMillionPlans: 0, visibility: 1 },
  input_ranges: { sensors: [0, 100000000], reportsPerHour: [0, 360000],
    airtimeMs: [0, 10000], costPerMillionAttempts: [0, 1000000000],
    incrementalCostPerMillionPlans: [0, 1000000000], visibility: [0, 1] },
  sources: [
    {title:'Analog Devices: industrial wireless sensor design', url:'https://www.analog.com/en/resources/analog-dialogue/articles/designing-your-smart-wireless-industrial-sensor.html',
      use:'Industrial interference and frequency hopping; one published deployment generated four packets per sensor every 30 seconds. Fleet size and pricing here are scenario inputs.'},
    {title:'Analog Devices: reliable low-power wireless sensor networks', url:'https://www.analog.com/en/resources/technical-articles/reliable-lo-power-wsn-for-iot.html',
      use:'Channel diversity and retransmission energy establish the operational motivation.'},
    {title:'NVIDIA: Sionna RT technical report', url:'https://research.nvidia.com/publication/2025-04_sionna-rt-technical-report',
      use:'GPU radio propagation and radio-map computation are deployment alternatives to individual availability calls.'},
    {title:'Semtech: long-range frequency hopping', url:'https://blog.semtech.com/lorawan-protocol-expands-network-capacity-with-new-long-range-frequency-hopping-spread-spectrum-technology',
      use:'Satellite and wide-area IoT use fragmented, coded packets; their packet-level objective requires an extension.'},
    {title:'DQI query-resource framework', url:'https://arxiv.org/html/2610.02145v1',
      use:'Oracle-query comparison framework. The local-check construction and finite bound are derived in this project.'}
  ],
  assumptions: [
    'Benchmark: independent, uniformly balanced hidden masks; separate coherent quantum membership calls and ordinary classical bit calls; no input-dependent advice or query history.',
    'Application choice is an engineering assessment. Measurements use synthetic masks and ideal native Qiskit circuits.',
    'Transfer model: one packet per hop; clear means successful; blocked means failed; retries encounter independently refreshed availability with the stated mean success rate.',
    'All transmission attempts have equal airtime and avoidable cost. Fixed gateway, staffing and infrastructure costs remain outside the calculation.',
    'One fresh six-hop DQI plan serves six transmission attempts. Incremental planning cost includes oracle construction, reversible evaluation, gates, error correction and readout above classical planning cost.',
    'Fleet size, airtime, transmission value and planning price are editable scenario inputs; currency values are USD scenarios, not measured customer savings or vendor quotes.',
    'Capacity gain and avoided-attempt savings are alternative uses of the same gain; the model does not add their values together.',
    'Hardware projection: independent three-hop windows, fixed 32-channel alphabet, constant ensemble score, linear parallel capacity. Twelve algorithm qubits can process windows serially.',
    'Visibility projection: a per-window mixture of ideal DQI outputs and uniform outputs. Visibility is a scenario parameter, not a measured gate fidelity.',
    'Readable or reusable availability maps select a different access regime: exact classical planning attained 100% on all 16 saved fixtures.'
  ]
};

export function normalizeScenario(input = {}) {
  const result = {};
  for (const [key, fallback] of Object.entries(QUERY_VALUE_MODEL.defaults)) {
    const raw = input[key];
    const value = raw === '' || raw === null || raw === undefined ? fallback : Number(raw);
    const [lo, hi] = QUERY_VALUE_MODEL.input_ranges[key];
    result[key] = Number.isFinite(value) ? Math.min(hi, Math.max(lo, value)) : fallback;
  }
  return result;
}

export function commercialValue(input = {}) {
  const x = normalizeScenario(input);
  const q = measured.summary.native_mean;
  const c = measured.summary.all_classical_ensemble_bound;
  const delivered = x.sensors * x.reportsPerHour * 24;
  const classicalAttempts = delivered / c;
  const quantumAttempts = delivered / q;
  const savedAttempts = classicalAttempts - quantumAttempts;
  const plans = quantumAttempts / 6;
  const gross = savedAttempts * 365 / 1e6 * x.costPerMillionAttempts;
  const premium = plans * 365 / 1e6 * x.incrementalCostPerMillionPlans;
  return {
    kind: 'scenario_transfer_from_measured_clear_hop_scores', inputs: x,
    quantum_mean: q, classical_reference: c,
    extra_clear_hops_per_million_attempts: (q-c)*1e6,
    relative_capacity_gain: q/c-1, relative_attempt_reduction: 1-c/q,
    delivered_packets_per_day: delivered, classical_attempts_per_day: classicalAttempts,
    quantum_attempts_per_day: quantumAttempts, saved_attempts_per_day: savedAttempts,
    aggregate_radio_hours_saved_per_day: savedAttempts*x.airtimeMs/3600000,
    quantum_six_hop_plans_per_day: plans,
    annual_gross_avoidable_cost_usd: gross, annual_incremental_planning_cost_usd: premium,
    annual_net_value_usd: gross-premium,
    break_even_incremental_usd_per_million_plans: 6*(q/c-1)*x.costPerMillionAttempts,
    measured_ci_transfer_attempt_reduction: measured.summary.instance_cluster_ci95.map(p=>1-c/p),
    measured_ci_transfer_extra_clear_hops_per_million: measured.summary.instance_cluster_ci95.map(p=>(p-c)*1e6)
  };
}

export function hardwareProjection(visibility = 1) {
  const v = normalizeScenario({visibility}).visibility;
  const ideal = .5+1/(2*Math.sqrt(3));
  const ceiling = measured.summary.all_classical_ensemble_bound;
  const score = .5+v*(ideal-.5);
  const oneQubitMean = measured.cases.reduce((sum,c)=>sum+c.quantum.resources.one_qubit_gates_per_output,0)/measured.cases.length/2;
  return {
    kind: 'analytic_product_code_projection', channels:32, per_window_visibility:v,
    ideal_ensemble_score:ideal, projected_clear_hop_score:score,
    classical_ensemble_ceiling:ceiling,
    break_even_visibility:(ceiling-.5)/(ideal-.5),
    rows:[2,8,20,100].map(windows=>({
      windows, algorithm_qubits:12*windows, decision_qubits:10*windows,
      physical_hops:3*windows, planning_queries_per_batch:3*windows,
      cx_per_batch:348*windows, one_qubit_gates_per_batch_estimate:oneQubitMean*windows,
      input_table_bits:96*windows, full_input_classical_local_assignments:1024*windows,
      projected_clear_hop_score:score,
      extra_clear_hops_per_batch:3*windows*(score-ceiling),
      capacity_gain:score/ceiling-1, physical_error_correction_qubits_included:false,
      quality_basis:'analytic ensemble; counts extrapolated from the compiled 32-channel blocks'
    })),
    alphabet_extension:[32,64,256,1024].map(channels=>({
      channels, algorithm_qubits_per_window:2*Math.log2(channels)+2,
      input_table_bits_per_window:3*channels,
      classical_ensemble_ceiling:.5+channels/(4*(channels-1)),
      ideal_ensemble_score:ideal,
      ideal_gap_percentage_points:100*(ideal-.5-channels/(4*(channels-1))),
      basis:'analytic balanced-mask extension; three separately counted oracle calls per window'
    }))
  };
}

export function queryCommercialSnapshot(input = {}) {
  const inputs = normalizeScenario(input);
  return {...QUERY_VALUE_MODEL, selected_scenario:commercialValue(inputs),
    hardware_projection:hardwareProjection(inputs.visibility),
    quantum_measurements_generated:false};
}
