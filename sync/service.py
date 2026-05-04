import urllib.request
import urllib.error
import json
import time


def get_config():
    from django.conf import settings
    return {
        'serveur_url': getattr(settings, 'SERVEUR_URL', 'http://127.0.0.1:8001'),
        'machine_id':  getattr(settings, 'MACHINE_ID', 'machine_01'),
        'token':       getattr(settings, 'SYNC_TOKEN', None),
    }


def reveiller_serveur(serveur_url):
    for tentative in range(3):
        try:
            urllib.request.urlopen(f'{serveur_url}/api/ping/', timeout=20)
            print("Serveur accessible.")
            return True
        except urllib.error.HTTPError:
            print("Serveur accessible (HTTP).")
            return True
        except Exception as e:
            print(f"Tentative {tentative + 1}/3 echouee : {e}")
            time.sleep(5)
    return False


def envoyer_donnees(serveur_url, token, machine_id, donnees):
    try:
        data = json.dumps({
            'machine_id': machine_id,
            'donnees':    donnees
        }, default=str).encode()

        req = urllib.request.Request(
            f'{serveur_url}/api/sync/',
            data=data,
            headers={
                'Content-Type':  'application/json',
                'Authorization': f'Token {token}'
            },
            method='POST'
        )
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f'Erreur envoi : {e}')
        return None


def telecharger_donnees(serveur_url, token):
    try:
        req = urllib.request.Request(
            f'{serveur_url}/api/descendante/',
            headers={
                'Content-Type':  'application/json',
                'Authorization': f'Token {token}'
            },
            method='GET'
        )
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f'Erreur telechargement : {e}')
        return None


def appliquer_donnees(donnees):
    """Applique les donnees du serveur sur la base locale (modeles Sprint 1)"""
    from produits.models import Produit, Categorie
    from ventes.models import Vente
    from depenses.models import Depense
    from accounts.models import Utilisateur

    stats = {
        'categories':   0,
        'produits':     0,
        'utilisateurs': 0,
        'ventes':       0,
        'depenses':     0,
    }

    # 1. Categories
    for c in donnees.get('categories', []):
        Categorie.objects.update_or_create(
            nom=c['nom'],
            defaults={
                'description': c.get('description', ''),
            }
        )
        stats['categories'] += 1

    # 2. Produits
    for p in donnees.get('produits', []):
        try:
            categorie = Categorie.objects.get(nom=p['categorie_nom'])
            Produit.objects.update_or_create(
                nom=p['nom'],
                defaults={
                    'categorie':      categorie,
                    'prix_achat':     p['prix_achat'],
                    'prix_vente':     p['prix_vente'],
                    'quantite_stock': p['quantite_stock'],  # ← Sprint 1
                    'seuil_alerte':   p['seuil_alerte'],
                    'actif':          p.get('actif', True),  # ← Sprint 1
                }
            )
            stats['produits'] += 1
        except Categorie.DoesNotExist:
            print(f"Categorie introuvable pour produit {p['nom']}")

    # 3. Utilisateurs
    for u in donnees.get('utilisateurs', []):
        utilisateur, created = Utilisateur.objects.get_or_create(
            username=u['username'],
            defaults={
                'first_name': u.get('first_name', ''),
                'last_name':  u.get('last_name', ''),
                'role':       u.get('role', 'GESTIONNAIRE'),
            }
        )
        if created:
            utilisateur.password = u['password_hash']
            utilisateur.save()
            stats['utilisateurs'] += 1

    # 4. Ventes
    for v in donnees.get('ventes', []):
        # Identification par produit + gestionnaire + date
        try:
            vendeur = Utilisateur.objects.get(username=v['gestionnaire_username'])
            produit = Produit.objects.get(nom=v['produit_nom'])

            Vente.objects.get_or_create(
                produit=      produit,
                gestionnaire= vendeur,
                date_vente=   v['date_vente'],
                defaults={
                    'quantite':      v['quantite'],
                    'prix_unitaire': v['prix_unitaire'],
                    'client':        v.get('client', ''),
                    'annulee':       v.get('annulee', False),
                }
            )
            stats['ventes'] += 1
        except (Utilisateur.DoesNotExist, Produit.DoesNotExist):
            pass

    # 5. Depenses
    for d in donnees.get('depenses', []):
        try:
            gestionnaire = Utilisateur.objects.get(
                username=d['gestionnaire_username']
            )
            Depense.objects.get_or_create(
                libelle=      d['libelle'],
                date_depense= d['date_depense'],
                defaults={
                    'categorie_depense': d['categorie_depense'],
                    'montant':           d['montant'],
                    'gestionnaire':      gestionnaire,
                }
            )
            stats['depenses'] += 1
        except Utilisateur.DoesNotExist:
            pass

    print(f"Donnees appliquees : {stats}")
    return stats


def synchroniser():
    """Sync bidirectionnelle : envoie local → serveur, puis serveur → local"""
    from produits.models import Produit, Categorie
    from ventes.models import Vente
    from depenses.models import Depense

    cfg = get_config()
    print(f"Serveur cible : {cfg['serveur_url']}")

    if not cfg['token']:
        return {'statut': 'erreur', 'message': 'Token non configure.'}

    print("Reveil du serveur...")
    if not reveiller_serveur(cfg['serveur_url']):
        return {'statut': 'offline', 'message': 'Serveur non accessible.'}

    # ── Données à envoyer (tout ce qui est local) ──────────────────────────
    categories = Categorie.objects.all()
    produits   = Produit.objects.filter(actif=True)       # ← Sprint 1
    ventes     = Vente.objects.filter(annulee=False)
    depenses   = Depense.objects.all()

    donnees_upload = {
        'categories': [
            {
                'nom':         c.nom,
                'description': c.description or '',
            }
            for c in categories
        ],
        'produits': [
            {
                'nom':            p.nom,
                'categorie_nom':  p.categorie.nom,   # ← nom au lieu de uuid
                'prix_achat':     float(p.prix_achat),
                'prix_vente':     float(p.prix_vente),
                'quantite_stock': p.quantite_stock,  # ← Sprint 1
                'seuil_alerte':   p.seuil_alerte,
                'actif':          p.actif,            # ← Sprint 1
            }
            for p in produits
        ],
        'ventes': [
            {
                'produit_nom':           v.produit.nom,
                'gestionnaire_username': v.gestionnaire.username,
                'quantite':              v.quantite,
                'prix_unitaire':         float(v.prix_unitaire),
                'montant_total':         float(v.montant_total),
                'date_vente':            str(v.date_vente),
                'client':                v.client or '',
                'annulee':               v.annulee,
            }
            for v in ventes
        ],
        'depenses': [
            {
                'libelle':               d.libelle,
                'categorie_depense':     d.categorie_depense,
                'montant':               float(d.montant),
                'gestionnaire_username': d.gestionnaire.username,
                'date_depense':          str(d.date_depense),
            }
            for d in depenses
        ],
    }

    # 1. Envoie vers le serveur
    resultat = envoyer_donnees(
        cfg['serveur_url'],
        cfg['token'],
        cfg['machine_id'],
        donnees_upload
    )
    print(f"Reponse serveur : {resultat}")

    # 2. Télécharge depuis le serveur
    print("Telechargement donnees serveur...")
    data = telecharger_donnees(cfg['serveur_url'], cfg['token'])

    if data and data.get('statut') == 'success':
        stats = appliquer_donnees(data['donnees'])
        return {
            'statut':  'success',
            'message': 'Synchronisation complete reussie !',
            'details': stats,
        }

    return {
        'statut':  'erreur',
        'message': f"Echec telechargement : {data}"
    }