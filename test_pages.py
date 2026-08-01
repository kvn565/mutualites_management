from django.test import Client
from core.models import Utilisateur

client = Client()
user = Utilisateur.objects.get(username='kevin_admin')
client.force_login(user)

response = client.get('/aide/')
content = response.content.decode('utf-8')
print('Page aide OK:', 'Centre d\'aide' in content)

response = client.get('/aide/messages/')
content = response.content.decode('utf-8')
print('Page messages OK:', 'Messages au SuperAdmin' in content)

response = client.get('/aide/documents/')
content = response.content.decode('utf-8')
print('Page documents OK:', 'Documents SuperAdmin' in content)