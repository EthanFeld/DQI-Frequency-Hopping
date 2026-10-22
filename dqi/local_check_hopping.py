"""DQI for q-ary local-check frequency hopping with explicit oracle accounting.

Two [3,2,2] single-parity-check codes over GF(32) generate six physical hops
(u,v,u+v) in two windows. The dual consists of two length-three repetition
codes. DQI coherently decodes one error in each window. The objective remains
the fraction of individual clear hops. Query advantage refers solely to a
balanced black-box availability ensemble with coherent membership access.
"""
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, transpile
from qiskit.circuit.library import StatePreparation, DiagonalGate

Q,H,BLOCKS=32,5,2
SLOTS=3*BLOCKS
DECISIONS=2*H*BLOCKS
QUBITS=DECISIONS+2*BLOCKS
METHODS=('knowledge_gradient','prange','posterior_candidate','random')


def make_task(seed):
    rng=np.random.default_rng(seed);mask=np.zeros((SLOTS,Q),np.uint8)
    for row in mask:row[rng.choice(Q,Q//2,replace=False)]=1
    return dict(seed=int(seed),allowed=mask.tolist(),physical_allowed=mask.tolist(),
        task='Clear physical hops with a local-check hopping code',
        code='Two q-ary [3,2,2] single-parity-check blocks over GF(32)',
        dual_code='Two length-three repetition codes',
        fixture='Independent uniformly balanced channel availability',
        physical_channels=Q,physical_hops=SLOTS,decision_qubits=DECISIONS,total_qubits=QUBITS,
        pairwise_collision_bound=SLOTS-2,per_changed_window_collision_bound=1,
        measured_rf_data=False,objective_changed=False,
        objective='Fraction of individual physical hops on clear channels',
        oracle_access_assumption='Availability accessible through coherent/basis membership calls; no mask advice to planners')


@lru_cache(None)
def local_words():
    ids=np.arange(Q*Q,dtype=np.uint16);u=ids&(Q-1);v=ids>>H
    words=np.column_stack([u,v,u^v]).astype(np.uint8);words.flags.writeable=False
    return words


def plan_words(identifier):
    return np.concatenate([local_words()[(int(identifier)>>(2*H*b))&((1<<(2*H))-1)] for b in range(BLOCKS)])


def score_ids(mask,identifiers):
    ids=np.asarray(identifiers,dtype=np.uint32);mask=np.asarray(mask,np.uint8)
    total=np.zeros(ids.shape,float)
    for b in range(BLOCKS):
        word=local_words()[(ids>>(2*H*b))&((1<<(2*H))-1)]
        total+=mask[np.arange(3)+3*b,word].sum(axis=-1)
    return total/SLOTS


def witness(task,identifier):
    word=plan_words(identifier);clear=np.asarray(task['allowed'])[np.arange(SLOTS),word]
    return dict(coefficient_id=int(identifier),physical_hops=word.tolist(),
        independent_symbols=[int(word[j]) for j in range(SLOTS) if j%3!=2],
        clear_hops=clear.tolist(),score=float(clear.mean()))


def _zero_match(circuit,wires,target):
    circuit.x(wires);circuit.mcx(wires,target);circuit.x(wires)


def build_block(mask):
    a=np.asarray(mask,np.uint8)
    assert a.shape==(3,Q) and np.all(a.sum(axis=1)==Q//2)
    c=QuantumCircuit(2*H+2);first=list(range(H));second=list(range(H,2*H));position=[2*H,2*H+1]
    weights=np.array([1/np.sqrt(2)]+[1/np.sqrt(6)]*3)
    c.append(StatePreparation(weights),position);c.h(first)
    phases=np.ones(4*Q,complex)
    for row in range(3):phases[np.arange(Q)|((row+1)<<H)]=2*a[row].astype(float)-1
    oracle=QuantumCircuit(H+2);oracle.append(DiagonalGate(phases),range(H+2))
    oracle=transpile(oracle,basis_gates=['rz','cx'],optimization_level=0)
    c.compose(oracle,qubits=first+position,inplace=True);c.h(first)
    # Sparse error syndromes: (e,0), (0,e), or (e,e).
    for a,b in zip(first,second):c.ccx(position[1],a,b)
    c.x(position[0])
    for a,b in zip(first,second):c.mcx(position+[b],a)
    c.x(position[0])
    # Code-only decoder: erase the address from zero/equal syndrome halves.
    _zero_match(c,second,position[0]);_zero_match(c,first,position[1])
    for a,b in zip(first,second):c.cx(a,b)
    _zero_match(c,second,position[0]);_zero_match(c,second,position[1])
    for a,b in reversed(list(zip(first,second))):c.cx(a,b)
    c.h(first+second)
    return c


def build_circuit(mask):
    mask=np.asarray(mask,np.uint8);c=QuantumCircuit(QUBITS)
    for b in range(BLOCKS):
        wires=list(range(2*H*b,2*H*(b+1)))+[DECISIONS+2*b,DECISIONS+2*b+1]
        c.compose(build_block(mask[3*b:3*b+3]),qubits=wires,inplace=True)
    c.metadata=dict(algorithm='DQI with local single-parity-check hopping code',
        decision_qubits=DECISIONS,total_qubits=QUBITS,queries_per_window=3,
        separately_counted_membership_calls=SLOTS,windows=BLOCKS,
        decoded_output_amplitudes_loaded=False,decoder_uses_availability=False,
        coherent_error_capacity='One error per triple; two independently decoded local errors',
        full_register_reduction=False,objective='Individual clear-hop fraction')
    return c


def expected_amplitudes(mask):
    amplitudes=np.array([1.]);mask=np.asarray(mask,np.uint8)
    for b in range(BLOCKS):
        local=mask[np.arange(3)+3*b,local_words()].sum(axis=1)
        amplitude=(1+(2*local.astype(float)-3)/np.sqrt(3))/np.sqrt(2*Q*Q)
        assert abs(float(amplitude@amplitude)-1)<1e-12
        amplitudes=np.kron(amplitude,amplitudes)
    return amplitudes


def resources(circuit,shots):
    primitive=transpile(circuit,basis_gates=['u','cx'],optimization_level=0,seed_transpiler=13)
    cx=int(primitive.count_ops().get('cx',0));one=int(primitive.count_ops().get('u',0))
    return dict(circuit.metadata,cx_per_output=cx,one_qubit_gates_per_output=one,
        total_cx_executions=cx*shots,raw_outputs=int(shots),independent_preparations=int(shots),
        planning_membership_calls_per_output=SLOTS,total_planning_queries=shots*SLOTS,
        postcommit_audit_queries_per_output=SLOTS,
        postcommit_scores_available_to_planner=False,
        oracle_table_entries_compiled=SLOTS*Q,oracle_table_bits=SLOTS*Q,
        oracle_build_counted_separately=True,simulator_wall_time_used_as_budget=False,
        coherent_receiver_hardware_measured=False,commercial_hardware_speedup_claim=False)


def analyze(task,counts):
    counts={str(k).replace(' ',''):int(v) for k,v in counts.items()};shots=sum(counts.values())
    ids=np.array([int(k,2) for k in counts],np.uint32);weights=np.array(list(counts.values()))
    dirty=int(weights[ids>=(1<<DECISIONS)].sum());assert dirty==0
    values=score_ids(task['allowed'],ids);mean=float(values@weights/shots)
    variance=float(((values-mean)**2)@weights/max(1,shots-1))
    return dict(shots=shots,raw_counts=counts,mean=mean,se=float(np.sqrt(variance/shots)),
        best=float(values.max()),best_witness=witness(task,int(ids[np.argmax(values)])),
        first_measured_witness=witness(task,int(ids[0])),workspace_failure_shots=dirty,
        best_of_shots_used_for_primary_comparison=False)


def simulate(task,shots=4096,seed=0,state_path=None):
    from qiskit_aer import AerSimulator
    source_hash=sha256(Path(__file__).read_bytes()).hexdigest()
    c=build_circuit(task['allowed']);ledger=resources(c,shots)
    backend=AerSimulator(method='matrix_product_state',matrix_product_state_truncation_threshold=0,
                         max_parallel_threads=2,mps_log_data=True)
    executable=transpile(c,backend=backend,optimization_level=0,seed_transpiler=13)
    executable.save_statevector(label='native')
    executable.save_matrix_product_state(label='native_mps')
    executable.add_register(ClassicalRegister(QUBITS,'readout'));executable.measure(range(QUBITS),range(QUBITS))
    result=backend.run(executable,shots=shots,seed_simulator=seed).result();assert result.success
    state=np.asarray(result.data()['native']);clean=state[:1<<DECISIONS]
    expected=expected_amplitudes(task['allowed']);anchor=int(np.argmax(abs(expected)))
    phase=expected[anchor]/clean[anchor];phase/=abs(phase)
    error=float(np.max(abs(clean*phase-expected)))
    dirty=float(np.vdot(state[1<<DECISIONS:],state[1<<DECISIONS:]).real)
    assert error<1e-10 and dirty<1e-12,(error,dirty)
    out=analyze(task,result.get_counts())
    out.update(quantum_execution=True,backend='Qiskit Aer matrix_product_state, truncation zero',
        resources=ledger,audit=dict(max_complex_amplitude_error=error,
            amplitudes_verified=1<<DECISIONS,workspace_failure_probability=dirty,
            native_norm=float(np.vdot(state,state).real),output_identity_used_to_generate_measurements=False),
        source_sha256=source_hash)
    if state_path:
        path=Path(state_path);gamma,lam=result.data()['native_mps']
        packed={f'g{i}_{bit}':np.asarray(pair[bit]) for i,pair in enumerate(gamma) for bit in (0,1)}
        packed.update({f'l{i}':np.asarray(value) for i,value in enumerate(lam)})
        packed['qubits']=np.array(QUBITS)
        np.savez_compressed(path,**packed)
        out.update(native_state_file=path.name,native_state_format='qiskit_aer_matrix_product_state',
                   native_state_sha256=sha256(path.read_bytes()).hexdigest())
    assert sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
    return out


def load_native_mps(path):
    """Contract saved native Aer tensors, independent of the DQI identity."""
    from threadpoolctl import threadpool_limits
    with np.load(path) as z,threadpool_limits(limits=2):
        n=int(z['qubits']);state=np.ones((1,1),complex)
        for i in range(n):
            state=np.concatenate([state@z[f'g{i}_0'],state@z[f'g{i}_1']],axis=0)
            if i<n-1:state*=z[f'l{i}'][None,:]
        return state[:,0]


@lru_cache(None)
def classical_bound(budget,failures=None):
    """Exact rational Bellman upper bound, including arbitrary adaptive queries.

    Relax every code restriction. A classical planner can return any channel
    per slot. -1 denotes a known clear channel; r>=0 counts queried blocked
    channels. Uniformly balanced unknown masks make all other channels
    exchangeable. This is an ENSEMBLE expectation bound, not a per-mask bound.
    """
    state=tuple(sorted((0,)*SLOTS if failures is None else failures))
    if budget==0 or all(x<0 for x in state):
        return sum(Fraction(1) if x<0 else Fraction(Q//2,Q-x) for x in state)/SLOTS
    options=[]
    for r in sorted(set(x for x in state if x>=0)):
        i=state.index(r);p=Fraction(Q//2,Q-r)
        yes=list(state);yes[i]=-1;no=list(state);no[i]+=1
        options.append(p*classical_bound(budget-1,tuple(sorted(yes)))+
            (1-p)*classical_bound(budget-1,tuple(sorted(no))))
    return max(options)


class MembershipOracle:
    def __init__(self,mask,budget):self.__mask=np.asarray(mask,np.uint8);self.budget=budget;self.log=[]
    def query(self,slot,channel):
        if len(self.log)>=self.budget:raise RuntimeError('Query budget exhausted')
        bit=int(self.__mask[slot,channel]);self.log.append([int(slot),int(channel),bit]);return bit


def beliefs(known):
    seen=(known>=0).sum(axis=1);positive=(known==1).sum(axis=1)
    prior=(Q/2-positive)/(Q-seen);table=np.where(known>=0,known,prior[:,None])
    means=[table[np.arange(3)+3*b,local_words()].sum(axis=1) for b in range(BLOCKS)]
    return means,prior


def classical_plan(oracle,seed,method='knowledge_gradient'):
    rng=np.random.default_rng(seed);known=np.full((SLOTS,Q),-1,np.int8);words=local_words()
    for step in range(oracle.budget):
        means,prior=beliefs(known)
        if method=='random':
            options=np.argwhere(known<0);slot,channel=options[int(rng.integers(len(options)))]
        elif method=='prange':
            targets=[j for j in range(SLOTS) if j%3!=2 and not np.any(known[j]==1)]
            if targets:
                slot=int(targets[0]);channel=int(rng.choice(np.flatnonzero(known[slot]<0)))
            else:
                options=[]
                for b,values in enumerate(means):
                    identifier=int(rng.choice(np.flatnonzero(np.isclose(values,values.max()))))
                    options.extend((3*b+j,int(words[identifier,j])) for j in range(3) if known[3*b+j,words[identifier,j]]<0)
                if not options:break
                slot,channel=options[int(rng.integers(len(options)))]
        elif method=='posterior_candidate':
            options=[]
            for b,values in enumerate(means):
                identifier=int(rng.choice(np.flatnonzero(np.isclose(values,values.max()))))
                options.extend((3*b+j,int(words[identifier,j])) for j in range(3) if known[3*b+j,words[identifier,j]]<0)
            if not options:break
            slot,channel=options[int(rng.integers(len(options)))]
        elif method=='knowledge_gradient':
            best=-np.inf;actions=[]
            for slot in range(SLOTS):
                b,j=divmod(slot,3);values=means[b];other_blocks=sum(float(x.max()) for k,x in enumerate(means) if k!=b)
                unseen=np.flatnonzero(known[slot]<0);remaining=len(unseen);p=prior[slot]
                known_values=values[known[slot,words[:,j]]>=0]
                best_known=float(known_values.max()) if len(known_values) else -np.inf
                grouped=np.full(Q,-np.inf);np.maximum.at(grouped,words[:,j],values)
                order=unseen[np.argsort(grouped[unseen])];top=int(order[-1]);runner=float(grouped[order[-2]])
                other=np.full(remaining,float(grouped[top]));other[unseen==top]=runner
                good=np.maximum.reduce([grouped[unseen]+1-p,other+(p-1)/(remaining-1),np.full(remaining,best_known)])
                bad=np.maximum.reduce([grouped[unseen]-p,other+p/(remaining-1),np.full(remaining,best_known)])
                values_after=p*good+(1-p)*bad+other_blocks;maximum=float(values_after.max())
                if maximum>best+1e-10:actions=[];best=maximum
                if maximum>=best-1e-10:
                    actions.extend((slot,int(x)) for x in unseen[np.isclose(values_after,best,rtol=0,atol=1e-10)])
            slot,channel=actions[int(rng.integers(len(actions)))]
        else:raise ValueError(method)
        known[slot,channel]=oracle.query(int(slot),int(channel))
    means,_=beliefs(known);identifier=0
    for b,values in enumerate(means):
        local=int(rng.choice(np.flatnonzero(np.isclose(values,values.max(),rtol=0,atol=1e-10))))
        identifier|=local<<(2*H*b)
    return dict(method=method,coefficient_id=identifier,queries=len(oracle.log),
        transcript=oracle.log,posterior_expected_score=sum(float(x.max()) for x in means)/SLOTS,
        public_local_assignments_examined=(len(oracle.log)+1)*BLOCKS*Q*Q,
        code_decomposition_exploited=True,seed=int(seed))


def full_input_optimum(task):
    mask=np.asarray(task['allowed'],np.uint8);identifier=0
    for b in range(BLOCKS):
        counts=mask[np.arange(3)+3*b,local_words()].sum(axis=1)
        identifier|=int(np.argmax(counts))<<(2*H*b)
    return dict(witness=witness(task,identifier),mask_entries_read=SLOTS*Q,
        local_assignments_examined=BLOCKS*Q*Q,certified_optimum=True,
        oracle_only_comparison=False)
