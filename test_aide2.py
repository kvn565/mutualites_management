from django.test import Client
from core.models import Utilisateur
import re

client = Client()
user = Utilisateur.objects.get(username='kevin_admin')
client.force_login(user)
response = client.get('/aide/')
content = response.content.decode('utf-8')

# Print the stats section
start = content.find('<!-- Stats rapides -->')
end = content.find('<!-- Cat')
if start != -1 and end != -1:
    print(content[start:end])
else:
    # Search for the stats cards
    idx = content.find('Articles publiés')
    if idx != -1:
        print(content[max(0,idx-200):idx+300])
    else:
        print("Not found: Articles publiés")