# Question answered: why do the failing targets of a fontc_crater ci run fail? Counts the
# failures of each result file by a short error signature (gftools' single-source mismatch,
# else the first compile_failed kind and command).
#   python3 classify_failures.py <out-A>/<run>.json [<out-B>/<run>.json ...]
import json, re, sys, collections
for path in sys.argv[1:]:
    d = json.load(open(path))
    fails = d['failure']
    sig = collections.Counter()
    for k, v in fails.items():
        s = json.dumps(v)
        if 'must match exactly one of' in s:
            m = re.search(r'matched (\d+)', s); key = 'single-source mismatch (matched %s)' % m.group(1)
        else:
            m = re.search(r'"kind": "([A-Za-z]+)"', s)
            key = (m.group(1) if m else s[:80])
        sig[key] += 1
    print(path.split('/')[-2], len(fails))
    for k, n in sig.most_common():
        print('  %3d %s' % (n, k))
