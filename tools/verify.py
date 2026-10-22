"""Verify the current upload's data, circuit, documentation and dependency closure."""
from fractions import Fraction
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sys

sys.dont_write_bytecode=True
PROJECT=Path(__file__).resolve().parents[1]
PUBLISH_ONLY_FILES={'.github/workflows/pages.yml','tools/build_pages.py'}
sys.path.insert(0,str(PROJECT))
from package import FILES,UPLOAD_FILE_LIMIT


def read_json(name):return json.loads((PROJECT/name).read_text(encoding='utf-8-sig'))


def rescore(record):
    q=record['quantum'];mask=record['task']['allowed'];total=0;weighted=0.;squared=0.
    assert len(mask)==6 and all(len(row)==32 and sum(row)==16 for row in mask)
    for bits,count in q['raw_counts'].items():
        value=int(bits,2);assert len(bits)==24 and value<2**20 and count>0
        u,v,w,z=[(value>>shift)&31 for shift in (0,5,10,15)]
        hops=(u,v,u^v,w,z,w^z)
        score=sum(mask[j][channel] for j,channel in enumerate(hops))/6
        total+=count;weighted+=count*score;squared+=count*score*score
    assert total==q['shots'] and math.isclose(weighted/total,q['mean'],abs_tol=1e-12)
    assert q['workspace_failure_shots']==0
    return weighted/total,total


def verify():
    import numpy as np
    from qiskit import transpile
    from qiskit.quantum_info import Statevector
    from dqi.local_check_hopping import build_block,build_circuit,classical_bound,full_input_optimum
    for name in FILES:
        assert (PROJECT/name).is_file(),name
        assert (PROJECT/name).stat().st_size<=UPLOAD_FILE_LIMIT,('Upload file exceeds 2 MB',name)
    extras=[path.relative_to(PROJECT).as_posix() for path in PROJECT.rglob('*')
            if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc'
            and '.git' not in path.relative_to(PROJECT).parts
            and path.relative_to(PROJECT).as_posix() not in (set(FILES)|PUBLISH_ONLY_FILES)]
    assert not extras,('Unexpected project files',extras)
    bank=read_json('data/checkcode_results.json');audit=read_json('data/checkcode_audit.json')
    javascript=(PROJECT/'data/checkcode_results.js').read_text(encoding='utf-8-sig')
    assert json.loads(javascript.removeprefix('export const CHECKCODE_RESULTS = ').strip().removesuffix(';'))==bank
    for name,digest in bank['source_hashes'].items():assert sha256((PROJECT/name).read_bytes()).hexdigest()==digest,name
    digest=sha256((PROJECT/'data/checkcode_results.json').read_bytes()).hexdigest()
    # Restore the original audited JSON formatting; compaction must preserve every value and key order.
    audited_bytes=(json.dumps(bank,indent=2)+'\n').replace('\n','\r\n').encode('utf-8')
    audited_digest=sha256(audited_bytes).hexdigest()
    assert audit['passed'] and audit['evidence_sha256']==audited_digest
    model=(PROJECT/'query_value.js').read_text(encoding='utf-8')
    assert f"measured_evidence_sha256: '{digest}'" in model
    assert f"audited_evidence_sha256: '{audited_digest}'" in model
    means=[];shots=0;total_cx=0;total_u=0
    guide=(PROJECT/'CIRCUITS.md').read_text(encoding='utf-8')
    for index,case in enumerate(bank['cases']):
        mean,n=rescore(case);means.append(mean);shots+=n
        primitive=transpile(build_circuit(case['task']['allowed']),basis_gates=['u','cx'],
                            optimization_level=0,seed_transpiler=13)
        ledger=case['quantum']['resources'];counts=primitive.count_ops()
        assert primitive.num_qubits==24 and set(counts)<={'u','cx'}
        assert counts['cx']==ledger['cx_per_output']==696
        assert counts['u']==ledger['one_qubit_gates_per_output']
        assert full_input_optimum(case['task'])['witness']['score']==1
        row=f"| {index+1} | {case['task']['seed']} | {mean*100:.3f}% | {counts['u']:,} | {951000+index} |"
        assert row in guide,('Circuit documentation differs',row)
        total_cx+=counts['cx']*n;total_u+=counts['u']*n
    assert len(means)==16 and shots==65536 and total_cx==45613056 and total_u==67805184
    mean=sum(means)/16;summary=bank['summary']
    assert math.isclose(mean,summary['native_mean'],abs_tol=1e-12)
    half=2.131449545559323*np.std(means,ddof=1)/4
    assert np.allclose([mean-half,mean+half],summary['instance_cluster_ci95'],rtol=0,atol=1e-12)
    upper=Fraction(1,2)+max(Fraction(16*(16-r),(32-r)*(31-r)) for r in range(16))
    assert upper==Fraction(47,62)==classical_bound(6)
    for record in read_json('data/checkcode_backend_runs.json')['runs']:
        _,count=rescore(record);assert count==512 and record['native_backend_calls']==1
        primitive=transpile(build_circuit(record['task']['allowed']),basis_gates=['u','cx'],
                            optimization_level=0,seed_transpiler=13)
        assert primitive.count_ops()['cx']==696 and primitive.count_ops()['u']==1041
        assert primitive.count_ops()['u']==record['quantum']['resources']['one_qubit_gates_per_output']
    # Audit a complete window without allocating a 24-qubit dense state.
    mask=np.asarray(bank['cases'][0]['task']['allowed'][:3],dtype=int)
    native=np.asarray(Statevector.from_instruction(build_block(mask)))
    ids=np.arange(1024);u=ids&31;v=ids>>5
    f=2*(mask[0,u]+mask[1,v]+mask[2,u^v])-3
    expected=(1+f/np.sqrt(3))/np.sqrt(2048)
    anchor=np.argmax(abs(expected));phase=expected[anchor]/native[anchor];phase/=abs(phase)
    error=float(np.max(abs(native[:1024]*phase-expected)))
    assert error<1e-10 and float(np.vdot(native[1024:],native[1024:]).real)<1e-12
    # Source and documentation references must stay within the clean project.
    links=0
    for name in FILES:
        path=PROJECT/name
        if path.suffix=='.js':
            for ref in re.findall(r"from\s+['\"]([^'\"]+)['\"]",path.read_text(encoding='utf-8-sig')):
                target=path.parent/ref if ref.startswith('.') else PROJECT/(ref.replace('.','/')+'.py')
                assert target.resolve().is_relative_to(PROJECT) and target.is_file(),(name,ref)
                links+=1
        if path.suffix=='.md':
            for ref in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
                if '://' in ref:continue
                relative=ref.split('#',1)[0]
                if relative:assert (path.parent/relative).is_file(),(name,ref)
    assert 'qiskit_aer' not in sys.modules,'Live imports must remain Aer-free'
    result=dict(passed=True,project_files=len(FILES),native_bank_outputs=shots,
        backend_replay_records_verified=2,all_fixture_gate_ledgers_and_docs_verified=True,
        clean_upload_dependencies_verified=links,independent_bound=str(upper),
        native_window_amplitude_max_error=error,measured_evidence_sha256=digest,
        original_audit_evidence_sha256=audited_digest,lossless_evidence_compaction_verified=True,
        upload_file_limit_bytes=UPLOAD_FILE_LIMIT,largest_upload_file_bytes=max((PROJECT/name).stat().st_size for name in FILES))
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':verify()
