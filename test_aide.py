from django.test import Client
from core.models import Utilisateur
import re

client = Client()
user = Utilisateur.objects.get(username='kevin_admin')
client.force_login(user)
response = client.get('/aide/')
content = response.content.decode('utf-8')

# Check for categories
cats = re.findall(r'<h6 class="mb-1">([^<]+)</h6>', content)
print('Found h6 mb-1:', cats[:10])

# Check for recent articles in list-group
items = re.findall(r'list-group-item[^>]*>.*?<h6 class="mb-1">([^<]+)</h6>', content, re.DOTALL)
print('Recent articles:', items[:5])

# Check for stats
if 'total_articles' in content:
    print('total_articles in context: YES')
else:
    print('total_articles in context: NO')

# Check for "Aucune catégorie"
if 'Aucune catégorie' in content:
    print('Shows: Aucune catégorie')
elif 'Catégories d\'aide' in content:
    print('Shows: Catégories d\'aide')
else:
    print('Unknown state')