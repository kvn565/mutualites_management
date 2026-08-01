import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mutualite.settings')
django.setup()

from django.db import connection
cursor = connection.cursor()

# 1. Migrations core appliquees en base
cursor.execute("SELECT id, app, name, applied FROM django_migrations WHERE app='core' ORDER BY id")
rows = cursor.fetchall()
print('=== Migrations core en base ===')
for r in rows:
    print(f'  id={r[0]:3d}  name={r[2]:50s}  applied={r[3]}')

# 2. Colonnes reelles de core_mutualite
cursor.execute("PRAGMA table_info(core_mutualite)")
cols = cursor.fetchall()
print()
print('=== Colonnes reelles de core_mutualite ===')
for c in cols:
    print(f'  cid={c[0]:2d}  name={c[1]:30s}  type={c[2]}')

# 3. Verifier si signature existe
has_sig = any(c[1] == 'signature' for c in cols)
print()
print(f'>>> Colonne signature presente: {has_sig}')
