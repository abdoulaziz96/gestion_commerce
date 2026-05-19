import os
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from google import genai
from google.genai import types


def get_donnees_boutique(user):
    """Récupère les données en temps réel selon le rôle."""
    from ventes.models import Vente
    from depenses.models import Depense
    from produits.models import Produit
    from django.db.models import Sum

    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)

    # Données communes
    produits_alerte = Produit.objects.filter(actif=True)
    produits_alerte = [p for p in produits_alerte if p.en_alerte]

    if user.role == 'ADMIN':
        # Admin voit tout
        ca_jour = Vente.objects.filter(
            date_vente__date=aujourd_hui, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        ca_mois = Vente.objects.filter(
            date_vente__date__gte=debut_mois, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        depenses_mois = Depense.objects.filter(
            date_depense__gte=debut_mois
        ).aggregate(t=Sum('montant'))['t'] or 0

        nb_ventes = Vente.objects.filter(
            date_vente__date__gte=debut_mois, annulee=False
        ).count()

    else:
        # Gestionnaire voit ses propres données
        ca_jour = Vente.objects.filter(
            gestionnaire=user,
            date_vente__date=aujourd_hui,
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        ca_mois = Vente.objects.filter(
            gestionnaire=user,
            date_vente__date__gte=debut_mois,
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        depenses_mois = Depense.objects.filter(
            gestionnaire=user,
            date_depense__gte=debut_mois
        ).aggregate(t=Sum('montant'))['t'] or 0

        nb_ventes = Vente.objects.filter(
            gestionnaire=user,
            date_vente__date__gte=debut_mois,
            annulee=False
        ).count()

    nb_produits_alerte = len(produits_alerte)
    noms_alerte = [p.nom for p in produits_alerte[:5]]

    return {
        'ca_jour': float(ca_jour),
        'ca_mois': float(ca_mois),
        'depenses_mois': float(depenses_mois),
        'benefice_net': float(ca_mois) - float(depenses_mois),
        'nb_ventes_mois': nb_ventes,
        'nb_produits_alerte': nb_produits_alerte,
        'produits_alerte': noms_alerte,
        'date': aujourd_hui.strftime('%d/%m/%Y'),
    }


def construire_prompt_systeme(user, donnees):
    """Construit le prompt système personnalisé."""
    role_label = "Administrateur" if user.role == 'ADMIN' else "Gestionnaire"

    return f"""Tu es IBRA, l'assistant intelligent de la boutique IBRAFRIK Decor, spécialisée en meubles, décoration, électroménager et équipement GYM à Malanville, Bénin.

Tu t'adresses à {user.get_full_name() or user.username}, qui est {role_label}.

DONNÉES EN TEMPS RÉEL DE LA BOUTIQUE ({donnees['date']}) :
- CA aujourd'hui : {donnees['ca_jour']:,.0f} FCFA
- CA ce mois : {donnees['ca_mois']:,.0f} FCFA
- Dépenses ce mois : {donnees['depenses_mois']:,.0f} FCFA
- Bénéfice net : {donnees['benefice_net']:,.0f} FCFA
- Nombre de ventes ce mois : {donnees['nb_ventes_mois']}
- Produits en alerte stock : {donnees['nb_produits_alerte']}
{f"- Produits concernés : {', '.join(donnees['produits_alerte'])}" if donnees['produits_alerte'] else ""}

GUIDE D'UTILISATION DE L'APPLICATION :
- /login/ : Connexion avec identifiant et mot de passe
- /dashboard/ : Tableau de bord gestionnaire avec KPI et graphiques
- /admin-dashboard/ : Vue globale administrateur
- /produits/ : Liste des produits avec onglet Catégories pour gérer les catégories
- /produits/ajouter/ : Ajouter un nouveau produit
- /ventes/enregistrer/ : Enregistrer une vente (déduit automatiquement du stock)
- /ventes/ : Historique de toutes les ventes avec filtres par date
- /depenses/ajouter/ : Enregistrer une dépense
- /stock/ : État du stock avec alertes de rupture
- /stock/entree/ : Entrée de stock (approvisionnement)
- /stock/inventaire/ : Faire l'inventaire complet
- /rapports/journalier/ : Rapport du jour avec export PDF
- /messagerie/ : Messagerie interne entre gestionnaire et administrateur
- /profil/ : Modifier ses informations personnelles et changer le mot de passe

RÈGLES DE COMPORTEMENT :
- Réponds toujours en français
- Sois concis, professionnel et chaleureux
- Utilise les données en temps réel pour répondre aux questions chiffrées
- Si on te demande une action que tu ne peux pas faire (modifier données), indique comment le faire dans l'application
- Ne partage jamais d'informations confidentielles d'un utilisateur à un autre
"""


@login_required
@csrf_exempt
def chatbot_query(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        body    = json.loads(request.body)
        message = body.get('message', '').strip()
        historique = body.get('historique', [])

        if not message:
            return JsonResponse({'error': 'Message vide'}, status=400)

        # Clé API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return JsonResponse({'error': 'Clé API non configurée'}, status=500)

        # Données boutique en temps réel
        donnees = get_donnees_boutique(request.user)

        # Client Gemini
        client = genai.Client(api_key=api_key)

        # Construire l'historique des messages
        messages = []
        for msg in historique[-10:]:  # 10 derniers messages max
            role    = 'user' if msg['role'] == 'user' else 'model'
            messages.append(types.Content(
                role=role,
                parts=[types.Part(text=msg['content'])]
            ))

        # Ajouter le nouveau message
        messages.append(types.Content(
            role='user',
            parts=[types.Part(text=message)]
        ))

        # ✅ Utilisation du modèle 'gemini-1.5-flash' (disponible et optimisé)
        response = client.models.generate_content(
            model='gemini-1.5-flash',  # ✅ Modèle disponible pour generateContent
            config=types.GenerateContentConfig(
                system_instruction=construire_prompt_systeme(
                    request.user, donnees
                ),
                max_output_tokens=500,
                temperature=0.7,
            ),
            contents=messages,
        )

        reponse_text = response.text or "Je n'ai pas pu générer une réponse."

        return JsonResponse({
            'reponse': reponse_text,
            'donnees': donnees,
        })

    except Exception as e:
        return JsonResponse({
            'reponse': f"Désolé, une erreur s'est produite : {str(e)}"
        }, status=200)