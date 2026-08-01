from django.test import Client
from core.models import Utilisateur
import re

client = Client()
user = Utilisateur.objects.get(username='kevin_admin')
client.force_login(user)

response = client.get('/dashboard/')
content = response.content.decode('utf-8')

# Check for Outils section in sidebar
outils_idx = content.find('Outils')
if outils_idx > 0:
    snippet = content[outils_idx:outils_idx+2000]
    print('Outils section found')
    # Look for aide links
    if 'aide:message_list' in snippet:
        print('Found aide:message_list')
    if 'aide:doc_superadmin_list' in snippet:
        print('Found aide:doc_superadmin_list')
    if 'aide:index' in snippet:
        print('Found aide:index')
    
    # Print the section
    print('--- Outils section ---')
    print(snippet[:1500])
else:
    print('Outils NOT found in sidebar')