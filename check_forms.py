import re
from django.test import Client
from django.contrib.auth import get_user_model
from core.models import Mutualite

User = get_user_model()
m = Mutualite.objects.first()
u = User.objects.filter(mutualite=m, role='ADMIN_MUTUALITE').first()
c = Client()
c.force_login(u)

pages = [
    ('/chambres/etablissements/nouveau/', 'Etablissement'),
    ('/chambres/services/nouveau/', 'Service'),
    ('/chambres/types/nouveau/', 'TypeChambre'),
    ('/chambres/chambres/nouvelle/', 'Chambre'),
    ('/chambres/hospitalisations/nouvelle/', 'Hospitalisation'),
    ('/chambres/hospitalisations/1/sortie/', 'Sortie'),
    ('/chambres/hospitalisations/1/soins/nouveau/', 'Soin'),
]

for p, name in pages:
    r = c.get(p)
    content = r.content.decode()
    inputs = re.findall(r'<input[^>]*type=["\'](text|date|datetime-local|number|email|tel|password)[\'"][^>]*>', content)
    selects = re.findall(r'<select[^>]*>', content)
    textareas = re.findall(r'<textarea[^>]*>', content)
    
    all_tags = inputs + selects + textareas
    missing = [t for t in all_tags if 'form-control' not in t and 'form-select' not in t]
    
    print(name + ': ' + str(len(all_tags)) + ' visible fields, ' + str(len(missing)) + ' missing classes')
    if missing:
        for m in missing[:3]:
            print('  MISSING: ' + m[:100])