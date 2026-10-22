"""Assemble the static GitHub Pages preview without changing the Qollab entrypoint."""
from pathlib import Path
import shutil
import sys

PROJECT=Path(__file__).resolve().parents[1]
DESTINATION=Path(sys.argv[1] if len(sys.argv)>1 else '_site').resolve()
if DESTINATION==PROJECT or DESTINATION.is_relative_to(PROJECT):
    raise ValueError('Pages output must stay outside the source project')
if DESTINATION.exists() and any(DESTINATION.iterdir()):
    raise FileExistsError(f'Pages output directory must be empty: {DESTINATION}')
DESTINATION.mkdir(parents=True,exist_ok=True)

for name in ('main.css','dashboard.js','query_frontpage.js','query_value.js',
             'README.md','CIRCUITS.md','LICENSE'):
    shutil.copy2(PROJECT/name,DESTINATION/name)

shell=(PROJECT/'index.html').read_text(encoding='utf-8')
(DESTINATION/'dashboard-shell.html').write_text(shell,encoding='utf-8')
preview=(PROJECT/'preview.html').read_text(encoding='utf-8')
(DESTINATION/'index.html').write_text(preview,encoding='utf-8')
javascript=(PROJECT/'preview.js').read_text(encoding='utf-8')
source="fetch('./index.html')"
assert javascript.count(source)==1
(DESTINATION/'preview.js').write_text(javascript.replace(source,"fetch('./dashboard-shell.html')"),encoding='utf-8')

data=DESTINATION/'data';data.mkdir()
for name in ('checkcode_results.js','checkcode_results.json','checkcode_audit.json','checkcode_backend_runs.json'):
    shutil.copy2(PROJECT/'data'/name,data/name)
(DESTINATION/'.nojekyll').write_text('',encoding='utf-8')
assert (DESTINATION/'index.html').is_file() and (data/'checkcode_results.js').is_file()
print(f'Built static DQI preview: {DESTINATION}')
