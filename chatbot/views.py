import os
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from anthropic import Anthropic


def get_donnees_boutique(user):
    from ventes.models import Vente
    from depenses.models import Depense
    from produits.models import Produit
    from django.db.models import Sum
    from datetime import timedelta

    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)
    semaine_debut        = aujourd_hui - timedelta(days=7)
    semaine_avant_debut  = semaine_debut - timedelta(days=7)

    produits_actifs = Produit.objects.filter(actif=True)
    produits_alerte = [p for p in produits_actifs if p.en_alerte]

    if user.role == 'ADMIN':
        ca_jour = Vente.objects.filter(
            date_vente__date=aujourd_hui, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        ca_mois = Vente.objects.filter(
            date_vente__date__gte=debut_mois, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        ca_semaine = Vente.objects.filter(
            date_vente__date__gte=semaine_debut, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        ca_semaine_derniere = Vente.objects.filter(
            date_vente__date__gte=semaine_avant_debut,
            date_vente__date__lt=semaine_debut,
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        depenses_mois = Depense.objects.filter(
            date_depense__gte=debut_mois
        ).aggregate(t=Sum('montant'))['t'] or 0

        nb_ventes = Vente.objects.filter(
            date_vente__date__gte=debut_mois, annulee=False
        ).count()

        derniere_vente = Vente.objects.filter(
            annulee=False
        ).order_by('-date_vente').first()

        derniere_vente_info = (
            f"{derniere_vente.gestionnaire.get_full_name()} "
            f"le {derniere_vente.date_vente.strftime('%d/%m à %H:%M')}"
        ) if derniere_vente else "Aucune vente enregistrée"

    else:
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

        ca_semaine = Vente.objects.filter(
            gestionnaire=user,
            date_vente__date__gte=semaine_debut,
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        ca_semaine_derniere = Vente.objects.filter(
            gestionnaire=user,
            date_vente__date__gte=semaine_avant_debut,
            date_vente__date__lt=semaine_debut,
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

        derniere_vente = Vente.objects.filter(
            gestionnaire=user, annulee=False
        ).order_by('-date_vente').first()

        derniere_vente_info = (
            f"le {derniere_vente.date_vente.strftime('%d/%m à %H:%M')}"
        ) if derniere_vente else "Aucune vente enregistrée"

    evolution = (
        "↗️ EN HAUSSE" if ca_semaine > ca_semaine_derniere
        else "↘️ EN BAISSE" if ca_semaine < ca_semaine_derniere
        else "→ STABLE"
    )

    details_alertes = [
        f"{p.nom} ({p.quantite_stock} restant(s))"
        for p in produits_alerte[:10]
    ]

    return {
        'ca_jour':            float(ca_jour),
        'ca_mois':            float(ca_mois),
        'ca_semaine':         float(ca_semaine),
        'ca_semaine_derniere': float(ca_semaine_derniere),
        'evolution_semaine':  evolution,
        'depenses_mois':      float(depenses_mois),
        'benefice_net':       float(ca_mois) - float(depenses_mois),
        'nb_ventes_mois':     nb_ventes,
        'nb_produits_alerte': len(produits_alerte),
        'produits_alerte':    details_alertes,
        'derniere_vente':     derniere_vente_info,
        'date':               aujourd_hui.strftime('%d/%m/%Y'),
        'mois':               aujourd_hui.strftime('%B %Y'),
    }


def construire_prompt_systeme(user, donnees):
    role_label = "Administrateur" if user.role == 'ADMIN' else "Gestionnaire"
    alertes_liste = (
        '\n'.join([f"  • {p}" for p in donnees['produits_alerte']])
        if donnees['produits_alerte']
        else "  • Aucun produit en alerte — stock OK ✅"
    )

    return f"""Tu es IBRA, l'assistant intelligent de la boutique IBRAFRIK Decor 🤖
Spécialisée en meubles, décoration maison, électroménager et équipement GYM à Cotonou, Bénin.
Tu t'adresses à {user.get_full_name() or user.username} ({role_label}).
Réponds TOUJOURS en français, de façon concise, professionnelle et chaleureuse.

=== DONNÉES EN TEMPS RÉEL ({donnees['date']}) ===
- CA aujourd'hui          : {donnees['ca_jour']:,.0f} FCFA
- CA ce mois ({donnees['mois']})  : {donnees['ca_mois']:,.0f} FCFA
- CA cette semaine        : {donnees['ca_semaine']:,.0f} FCFA {donnees['evolution_semaine']}
- CA semaine dernière     : {donnees['ca_semaine_derniere']:,.0f} FCFA
- Dépenses ce mois        : {donnees['depenses_mois']:,.0f} FCFA
- Bénéfice net            : {donnees['benefice_net']:,.0f} FCFA
- Ventes ce mois          : {donnees['nb_ventes_mois']} transactions
- Dernière vente          : {donnees['derniere_vente']}
- Produits en alerte      : {donnees['nb_produits_alerte']}
{alertes_liste}

=== GUIDE D'UTILISATION ===
- Ajouter produit       → /produits/ajouter/ — remplir nom, catégorie, prix, quantité
- Modifier produit      → /produits/ → icône crayon ✏️ sur la ligne
- Modifier prix         → /produits/ → icône crayon → changer prix achat/vente → Enregistrer
- Enregistrer vente     → /ventes/enregistrer/ → produit, quantité, prix → Valider
- Annuler vente         → /ventes/ → icône ❌ (stock remis automatiquement)
- Entrée stock          → /stock/entree/ → produit + quantité reçue
- Sortie stock          → /stock/sortie/ → pour pertes ou casses
- Inventaire            → /stock/inventaire/ → corriger toutes les quantités
- Rapport jour PDF      → /rapports/journalier/ → bouton PDF
- Rapport mensuel       → /rapports/mensuel/ → choisir mois et année
- Ajouter dépense       → /depenses/ajouter/ → libellé, catégorie, montant, date
- Envoyer message       → /messagerie/envoyer/ → choisir destinataire
- Changer mot de passe  → /profil/ → onglet Sécurité
- Gérer catégories      → /produits/ → onglet Catégories
- Mode jour/nuit        → bouton en bas de la sidebar

=== TES CAPACITÉS ===
1. Support technique  : Guide pas à pas sur l'utilisation de l'application
2. Analyse métier     : Chiffres en temps réel (CA, dépenses, bénéfice, comparaisons)
3. Alertes stock      : Signaler et lister les produits en rupture
4. Conseils proactifs : Suggérer des actions selon les données

Tu ne peux PAS modifier les données directement — guide vers la bonne page."""


@login_required
@csrf_exempt
def chatbot_init(request):
    """Message de bienvenue enrichi au chargement du chatbot."""
    try:
        donnees    = get_donnees_boutique(request.user)
        role_label = "Administrateur" if request.user.role == 'ADMIN' else "Gestionnaire"
        alertes_liste = (
            '\n'.join([f"  • {p}" for p in donnees['produits_alerte']])
            if donnees['produits_alerte']
            else "  • Aucun produit en alerte ✅"
        )

        salutation = f"""Bonjour {request.user.get_full_name() or request.user.username} ! 👋

Je suis **IBRA**, votre assistant IBRAFRIK Decor.
Vous êtes connecté en tant que **{role_label}**.

📊 **Situation du {donnees['date']}** :
- CA aujourd'hui : {donnees['ca_jour']:,.0f} FCFA
- CA ce mois : {donnees['ca_mois']:,.0f} FCFA
- CA cette semaine : {donnees['ca_semaine']:,.0f} FCFA {donnees['evolution_semaine']}
- Bénéfice net : {donnees['benefice_net']:,.0f} FCFA
- Ventes ce mois : {donnees['nb_ventes_mois']}

⚠️ **Alertes stock ({donnees['nb_produits_alerte']} produit(s))** :
{alertes_liste}

💬 **Je peux vous aider à :**
- Consulter vos chiffres en temps réel
- Guider l'utilisation de l'application
- Identifier les produits en rupture
- Comparer les performances semaine/mois

Posez-moi vos questions ! 😊"""

        return JsonResponse({
            'reponse':        salutation,
            'donnees':        donnees,
            'message_initial': True,
        })

    except Exception as e:
        return JsonResponse({
            'reponse': f"Bonjour ! Je suis IBRA, votre assistant. Comment puis-je vous aider ?"
        }, status=200)


@login_required
@csrf_exempt
def chatbot_query(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        body       = json.loads(request.body)
        message    = body.get('message', '').strip()
        historique = body.get('historique', [])

        if not message:
            return JsonResponse({'error': 'Message vide'}, status=400)

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return JsonResponse({
                'reponse': '❌ Clé API non configurée. Ajoutez ANTHROPIC_API_KEY dans les variables d\'environnement.'
            }, status=200)

        donnees = get_donnees_boutique(request.user)
        client  = Anthropic(api_key=api_key)

        # Construire l'historique — format Claude (assistant, pas model)
        messages = []
        for msg in historique[-10:]:
            role = 'user' if msg['role'] == 'user' else 'assistant'
            messages.append({'role': role, 'content': msg['content']})

        messages.append({'role': 'user', 'content': message})

        # Appel Claude Haiku — rapide et économique
        response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=500,
            system=construire_prompt_systeme(request.user, donnees),
            messages=messages,
        )

        return JsonResponse({
            'reponse': response.content[0].text,
            'donnees': donnees,
        })

    except Exception as e:
        err = str(e)
        if '401' in err or 'authentication' in err.lower():
            msg = '❌ Clé API invalide. Vérifiez ANTHROPIC_API_KEY.'
        elif '429' in err:
            msg = '⚠️ Trop de requêtes. Réessayez dans quelques secondes.'
        elif '529' in err or 'overloaded' in err.lower():
            msg = '⚠️ Service temporairement surchargé. Réessayez dans un instant.'
        else:
            msg = '⚠️ Erreur temporaire. Réessayez dans un instant.'
        return JsonResponse({'reponse': msg}, status=200)