#!/usr/bin/env python3
import subprocess

for proj in ['geography-kg-qa', 'education-kg-qa']:
    d = f'/mnt/e/hermes_code_workspace/{proj}'
    r = subprocess.run(
        ['docker', 'compose', 'up', '-d', '--no-deps', 'backend'],
        cwd=d, capture_output=True, text=True, timeout=60
    )
    print(f'{proj}: rc={r.returncode}')
    if r.stdout:
        print(f'  stdout: {r.stdout.strip()}')
    if r.stderr:
        print(f'  stderr: {r.stderr.strip()}')

print('DONE')
