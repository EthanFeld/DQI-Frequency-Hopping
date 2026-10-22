"""Qollab selected-backend adapter for local-check DQI membership experiments."""
import json
from qiskit import ClassicalRegister,transpile
from dqi.local_check_hopping import (make_task,build_circuit,resources,analyze,
    full_input_optimum,classical_bound,QUBITS)


def backend_info(backend):
    name=getattr(backend,'name',type(backend).__name__)
    name=name() if callable(name) else str(name)
    model=getattr(backend,'noise_model',None) or getattr(getattr(backend,'options',None),'noise_model',None)
    supported=('basic' in name.lower() or 'aer' in name.lower()) and not model
    return json.dumps(dict(name=name,live_supported=bool(supported),decision_qubits=20,
        total_qubits=24,task='Local-check frequency hopping',
        reason='This circuit requires an ideal Qiskit BasicSimulator or Aer simulator with 24-qubit capacity. Saved evidence remains available.'))


def live_job(backend,shots=512,seed=941001):
    shots,seed=int(shots),int(seed)
    if not 1<=shots<=4096:raise ValueError('Choose 1 to 4096 raw outputs')
    info=json.loads(backend_info(backend))
    if not info['live_supported']:raise ValueError(info['reason'])
    task=make_task(seed);circuit=build_circuit(task['allowed']);ledger=resources(circuit,shots)
    # Primitive gates avoid hidden large matrix operations in BasicSimulator.
    circuit=transpile(circuit,basis_gates=['u','cx'],optimization_level=0,seed_transpiler=13)
    circuit.add_register(ClassicalRegister(QUBITS,'hopping'))
    circuit.measure(range(QUBITS),range(QUBITS))
    result=backend.run(circuit,shots=shots,seed_simulator=seed).result()
    if not result.success:raise RuntimeError(str(result.status))
    quantum=analyze(task,result.get_counts())
    assert quantum['shots']==shots
    quantum.update(quantum_execution=True,backend=info['name'],resources=ledger,
        decoded_output_amplitudes_loaded=False,statevector_audit_performed_this_run=False)
    return json.dumps(dict(complete=True,kind='live_checkcode',task=task,quantum=quantum,
        full_input_classical=full_input_optimum(task),native_backend_calls=1,
        classical_ensemble_query_bound=float(classical_bound(6)),
        fixed_fixture_replay=True,advantage_claim_uses_heldout_ensemble=True,
        source_of_membership_gates='Classically compiled input availability table',
        coherent_availability_hardware_measured=False,commercial_hardware_speedup_demonstrated=False,
        simulator_wall_time_used_as_budget=False,predictions_included=False))
