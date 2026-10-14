"""
Test auto Niveaux 1+2 — methodedesecurite.txt
Usage: python test_security.py
Ne modifie rien, lecture seule.
"""
import os, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
APPS = ['affilies','ayants_droit','factures','cotisations','core','partenaires',
        'portail_partenaire','mutualite','single_tenant','comptabilite']

def scan(pattern, label):
    rx = re.compile(pattern)
    hits = []
    for app in APPS:
        p = BASE / app
        if not p.exists():
            continue
        for f in p.rglob('*.py'):
            try:
                txt = f.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{f.relative_to(BASE)}:{i}: {line.strip()[:120]}")
    status = "FAIL" if hits else "PASS"
    print(f"\n[{status}] {label} ({len(hits)} trouvés)")
    for h in hits[:20]:
        print(f"  - {h}")
    return len(hits) == 0

def check_deploy():
    print("\n=== Niveau 2 : check --deploy ===")
    os.system("python manage.py check --deploy")

def main():
    print("=== Niveau 1 : statique ===")
    ok = True
    ok &= scan(r"\.raw\s*\(\s*f['\"]|\.extra\s*\(|cursor\.execute\s*\(\s*f['\"]", "Anti-Injection SQL (B608)")
    ok &= scan(r"mark_safe\s*\(|autoescape\s+off", "Anti-XSS mark_safe/autoescape")
    # |safe dans templates
    safes = []
    for html in BASE.rglob("*.html"):
        try:
            txt = html.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if "|safe" in txt:
            safes.append(str(html.relative_to(BASE)))
    print(f"\n[INFO] Templates avec |safe : {len(safes)} (à revoir manuellement, ex. aide/article.html)")
    for s in safes[:20]:
        print(f"  - {s}")
    ok &= scan(r"@csrf_exempt", "Anti-CSRF csrf_exempt")
    ok &= scan(r"os\.system\s*\(.*request|subprocess\.(call|run|Popen)\s*\(.*request|eval\s*\(\s*request|exec\s*\(\s*request", "Anti-Command Injection (B602)")
    # secrets
    settings = (BASE / "mutualite" / "settings.py").read_text(encoding='utf-8', errors='ignore')
    if "django-insecure-dev-key" in settings:
        print("\n[FAIL] Secrets : SECRET_KEY fallback dev présent dans settings.py")
        ok = False
    else:
        print("\n[PASS] Secrets : pas de fallback insecure")
    # open redirect
    ok_redirect = scan(r"redirect\s*\(\s*request\.(GET|POST)\.get\s*\(\s*['\"]next", "Open Redirect ?next non validé")
    check_deploy()
    print("\nTerminé. Corrigez les FAIL avant prod.")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
