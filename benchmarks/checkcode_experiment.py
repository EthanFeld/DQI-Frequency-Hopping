"""Frozen held-out test of local-check DQI under a membership-query resource model."""
import json
import secrets
import sys
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import numpy as np
from scipy.stats import t as student_t

PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT))
from dqi.local_check_hopping import (make_task,simulate,MembershipOracle,classical_plan,
    classical_bound,score_ids,full_input_optimum,METHODS,SLOTS,Q,DECISIONS,QUBITS)


def run():
    # Solvers are fixed before private test-mask seeds are drawn. Seeds are
    # retained for replay, never passed through either planner interface.
    hashes={name:sha256((PROJECT/name).read_bytes()).hexdigest() for name in
            ('dqi/local_check_hopping.py','benchmarks/checkcode_experiment.py')}
    protocol=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        fixture_seeds=[secrets.randbits(52) for _ in range(16)],
        quantum_shots_per_fixture=4096,classical_trials_per_method_per_fixture=256,
        classical_methods=list(METHODS),planning_queries_per_output=SLOTS,
        postcommit_evaluator_queries_per_output=SLOTS,
        evaluator_information_returned_to_planner=False,
        scalar_objective_preserved=True,private_fixture_seeds_available_to_planners=False,
        primary_metric='Expected clear-hop fraction after six separately counted availability queries',
        primary_classical_control='Exact upper bound for all adaptive classical planners, even without code restrictions',
        selected_best_quantum_shot_is_primary_metric=False,
        oracle_assumption='Separate coherent quantum membership oracles; basis queries for classical planners',
        full_input_preprocessing_free=False,oracle_table_build_entries=Q*SLOTS,
        oracle_build_cost_included_in_separate_ledger=True,
        end_to_end_hardware_advantage_claim=False,
        source_hashes=hashes,discard_failed_fixtures=False)
    (PROJECT/'data/checkcode_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    cases=[]
    for index,seed in enumerate(protocol['fixture_seeds']):
        task=make_task(seed)
        quantum=simulate(task,shots=protocol['quantum_shots_per_fixture'],seed=951000+index,
            state_path=PROJECT/f'data/checkcode_native_{index:02}.npz')
        controls={}
        for method in METHODS:
            trials=[]
            for trial in range(protocol['classical_trials_per_method_per_fixture']):
                record=classical_plan(MembershipOracle(task['allowed'],SLOTS),
                    952000+index*1000+trial,method)
                record['score']=float(score_ids(task['allowed'],[record['coefficient_id']])[0])
                trials.append(record)
            values=np.array([r['score'] for r in trials])
            controls[method]=dict(mean=float(values.mean()),se=float(values.std(ddof=1)/np.sqrt(len(values))),
                outputs=len(values),total_queries=sum(r['queries'] for r in trials),trials=trials)
        record=dict(task=task,quantum=quantum,classical=controls,
            full_input_classical=full_input_optimum(task))
        path=PROJECT/f'data/checkcode_case_{index:02}.json';path.write_text(json.dumps(record,separators=(',',':'))+'\n')
        record['raw_file']=path.name;record['raw_sha256']=sha256(path.read_bytes()).hexdigest()
        for value in controls.values():value.pop('trials')
        cases.append(record)
        print(json.dumps(dict(case=index+1,quantum_mean=quantum['mean'],
            classical={method:row['mean'] for method,row in controls.items()},
            cx_per_output=quantum['resources']['cx_per_output'])),flush=True)
    means=np.array([c['quantum']['mean'] for c in cases]);average=float(means.mean())
    error=float(student_t.ppf(.975,len(cases)-1)*means.std(ddof=1)/np.sqrt(len(cases)))
    bound=classical_bound(SLOTS)
    summary=dict(native_outputs=sum(c['quantum']['shots'] for c in cases),fixtures=len(cases),
        native_mean=average,instance_cluster_ci95=[average-error,average+error],
        quantum_conditional_shot_se=float(np.sqrt(sum(c['quantum']['se']**2 for c in cases))/len(cases)),
        all_classical_ensemble_bound=float(bound),classical_bound_fraction=str(bound),
        observed_gap_percentage_points=100*(average-float(bound)),
        finite_query_advantage_supported=bool(average-error>float(bound)),
        query_advantage_scope='Balanced black-box availability ensemble with coherent membership access',
        all_classical_bound_applies_to_ensemble_not_each_exposed_mask=True,
        classical_method_means={m:float(np.mean([c['classical'][m]['mean'] for c in cases])) for m in METHODS},
        mean_full_input_classical_optimum=float(np.mean([c['full_input_classical']['witness']['score'] for c in cases])),
        scalar_objective_preserved=True,full_input_optimization_advantage=False,
        commercial_hardware_speedup_demonstrated=False)
    evidence=dict(schema_version=1,complete=True,executed=True,predictions_included=False,
        code='Direct sum of two GF(32) [3,2,2] local-check codes',
        decision_qubits=DECISIONS,total_qubits=QUBITS,physical_channels=Q,physical_hops=SLOTS,
        protocol=protocol,cases=cases,summary=summary,source_hashes=hashes)
    for name,digest in hashes.items():assert sha256((PROJECT/name).read_bytes()).hexdigest()==digest
    output=json.dumps(evidence,indent=2)+'\n'
    (PROJECT/'data/checkcode_results.json').write_text(output)
    (PROJECT/'data/checkcode_results.js').write_text('export const CHECKCODE_RESULTS = '+output.strip()+';\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':run()
