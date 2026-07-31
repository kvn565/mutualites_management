# core/services.py
# Services externes — vérification du NIF auprès de l'OBR.
import requests

OBR_URL = "https://obr.bi/index.php/component/odvc/?option=com_odvc&view=odvc&id=1"
OBR_TIMEOUT = 15


def verifier_nif_obr(nif):
    """
    Interroge le site de l'OBR pour retrouver le nom légal du contribuable.

    Retourne un dict :
        {'ok': True,  'nom': str}        si le NIF existe sur l'OBR
        {'ok': False, 'error': str}      sinon (NIF inconnu, erreur réseau, ...)
    """
    nif = (nif or '').strip()
    if not nif:
        return {'ok': False, 'error': 'NIF requis'}

    payload = {
        "option": "com_odvc",
        "view": "odvc",
        "id": "1",
        "type_doc": "4",
        "nif": nif,
        "Rechercher": "Vérifier",
    }

    try:
        resp = requests.post(OBR_URL, data=payload, timeout=OBR_TIMEOUT)
        resp.encoding = 'utf-8'
        html = resp.text

        search_str = "appartient à <b>"
        start = html.find(search_str)
        if start != -1:
            start += len(search_str)
            end = html.find("</b>", start)
            nom = html[start:end].strip()
            if nom:
                return {'ok': True, 'nom': nom}

        return {'ok': False, 'error': 'NIF non trouvé sur OBR'}
    except requests.RequestException as e:
        return {'ok': False, 'error': f"Erreur de connexion à l'OBR : {e}"}
