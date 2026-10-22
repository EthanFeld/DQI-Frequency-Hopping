"""Package only the current DQI deliverable; byte-check the ZIP."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode=True
PROJECT=Path(__file__).resolve().parents[1]
UPLOAD_FILE_LIMIT=2_000_000
FILES=(
    'README.md','CIRCUITS.md','LICENSE','index.html','main.js','main.css',
    'dashboard.js','query_frontpage.js','query_value.js','preview.html','preview.js',
    'dqi/__init__.py','dqi/checkcode_ui.py','dqi/local_check_hopping.py',
    'data/checkcode_results.js','data/checkcode_results.json','data/checkcode_audit.json',
    'data/checkcode_backend_runs.json','benchmarks/checkcode_experiment.py',
    'tools/package.py','tools/verify.py','tools/serve.py',
)


def package(destination=None):
    destination=Path(destination) if destination else PROJECT.parents[1]/'dqi-hop-qollab-js.zip'
    for name in FILES:
        assert (PROJECT/name).is_file(),f'Missing upload file: {name}'
        size=(PROJECT/name).stat().st_size
        if size>UPLOAD_FILE_LIMIT:
            raise ValueError(f'Qollab file limit exceeded: {name} is {size:,} bytes; maximum {UPLOAD_FILE_LIMIT:,}')
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name in FILES:archive.write(PROJECT/name,name)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist())==set(FILES)
        for name in FILES:
            assert archive.getinfo(name).file_size<=UPLOAD_FILE_LIMIT,name
            assert archive.read(name)==(PROJECT/name).read_bytes(),name
    largest=max(FILES,key=lambda name:(PROJECT/name).stat().st_size)
    result=dict(path=str(destination),files=len(FILES),bytes=destination.stat().st_size,
        per_file_limit_bytes=UPLOAD_FILE_LIMIT,largest_file=largest,largest_file_bytes=(PROJECT/largest).stat().st_size,
        sha256=sha256(destination.read_bytes()).hexdigest(),all_archive_files_match_source=True)
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':package(sys.argv[1] if len(sys.argv)>1 else None)
