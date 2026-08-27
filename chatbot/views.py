import json
import os
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from groq import Groq


def get_donnees_boutique(user):
  from depenses.models import Depense
  from produits.models import Produit
  from ventes.models import Vente

  aujourd_hui = timezone.now().date()
  debut_mois = aujourd_hui.replace(day=1)
  semaine_debut = aujourd_hui - timedelta(days=7)
  semaine_avant_debut = semaine_debut - timedelta(days=7)

  produits_actifs = Produit.objects.filter(actif=True)
  produits_alerte = [p for p in produits_actifs if p.en_alerte]

  if user.role == 'ADMIN':
    ca_jour = (
        Vente.objects.filter(
            date_vente__date=aujourd_hui, annulee=False
        ).aggregate(t=Sum('montant_total'))['t']
        or 0
    )

    ca_mois = (
        Vente.objects.filter(
            date_vente__date__gte=debut_mois, annulee=False
        ).aggregate(t=Sum('montant_total'))['t']
        or 0
    )

    ca_semaine = (
        Vente.objects.filter(
            date_vente__date__gte=semaine_debut, annulee=False
        ).aggregate(t=Sum('montant_total'))['t']
        or 0
    )

    ca_semaine_derniere = (
        Vente.objects.filter(
            date_vente__date__gte=semaine_avant_debut,
            date_vente__date__lt=semaine_debut,
            annulee=False,
        ).aggregate(t=Sum('montant_total'))['t']
        or 0
    )

    depenses_mois = (
        Depense.objects.filter(date_depense__gte=debut_mois).aggregate(
            t=Sum('montant')
        )['t']
        or 0
    )

    nb_ventes = Vente.objects.filter(
        date_vente__date__gte=debut_mois, annulee=False
    ).count()

    derniere_vente = (
        Vente.objects.filter(annulee=False).order_by('-date_vente').first()
    )
    derniere_vente_info = (
        f'{derniere_vente.gestionnaire.get_full_name()} le'
        f" {derniere_vente.date_vente.strftime('%d/%m à %H:%M')}"
        if derniere_vente
        else 'Aucune vente enregistrée'
    )

  else:
    ca_jour = (
        Vente.objects.filter(
            gestionnaire=user, date_vente__date=aujourd_hui, annulee=False
        ).aggregate(t=Sum('montant_total'))['t']
        or 0
    )

    ca_mois = (
        Vente.objects.filter(
            gestionnaire=user, date_vente__date__gte=debut_mois, annulee=False
        ).aggregate(t=Sum('montant_total'))['t']
        or 0
    )

    ca_semaine = (
        Vente.objects.filter(
            gestionnaire=user, date_vente__date__gte=semaine_debut, annulee=False
        ).aggregate(t=Sum('montant_total'))['t']
        or 0
    )

    ca_semaine_derniere = (
        Vente.objects.filter(
            gestionnaire=user,
            date_vente__date__gte=semaine_avant_debut,
            date_vente__date__lt=semaine_debut,
            annulee=False,
        ).aggregate(t=Sum('montant_total'))['t']
        or 0
    )

    depenses_mois = (
        Depense.objects.filter(
            gestionnaire=user, date_depense__gte=debut_mois
        ).aggregate(t=Sum('montant'))['t']
        or 0
    )

    nb_ventes = Vente.objects.filter(
        gestionnaire=user, date_vente__date__gte=debut_mois, annulee=False
    ).count()

    derniere_vente = (
        Vente.objects.filter(gestionnaire=user, annulee=False)
        .order_by('-date_vente')
        .first()
    )
    derniere_vente_info = (
        f"le {derniere_vente.date_vente.strftime('%d/%m à %H:%M')}"
        if derniere_vente
        else 'Aucune vente enregistrée'
    )

  evolution = (
      '↗️ EN HAUSSE'
      if ca_semaine > ca_semaine_derniere
      else '↘️ EN BAISSE'
      if ca_semaine < ca_semaine_derniere
      else '→ STABLE'
  )

  details_alertes = [
      f'{p.nom} ({p.quantite_stock} restant(s))' for p in produits_alerte[:10]
  ]

  return {
      'ca_jour': float(ca_jour),
      'ca_mois': float(ca_mois),
      'ca_semaine': float(ca_semaine),
      'ca_semaine_derniere': float(ca_semaine_derniere),
      'evolution_semaine': evolution,
      'depenses_mois': float(depenses_mois),
      'benefice_net': float(ca_mois) - float(depenses_mois),
      'nb_ventes_mois': nb_ventes,
      'nb_produits_alerte': len(produits_alerte),
      'produits_alerte': details_alertes,
      'derniere_vente': derniere_vente_info,
      'date': aujourd_hui.strftime('%d/%m/%Y'),
      'mois': aujourd_hui.strftime('%B %Y'),
  }


def construire_prompt_systeme(user, donnees):
  role_label = 'Administrateur' if user.role == 'ADMIN' else 'Gestionnaire'
  alertes_liste = (
      '\n'.join([f'  • {p}' for p in donnees['produits_alerte']])
      if donnees['produits_alerte']
      else '  • Aucun produit en alerte — stock OK ✅'
  )

  return f"""Tu es IBRA, l'assistant intelligent de la boutique IBRAFRIK Decor.
Spécialisée en meubles, décoration, électroménager et GYM à Cotonou, Bénin.
Tu t'adresses à {user.get_full_name() or user.username} ({role_label}).
Réponds TOUJOURS en français, de façon concise et professionnelle.

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
- Ajouter produit        → /produits/ajouter/
- Modifier produit/prix → /produits/ → icône crayon ✏️
- Enregistrer vente     → /ventes/enregistrer/
- Annuler vente         → /ventes/ → icône ❌
- Entrée stock          → /stock/entree/
- Sortie stock          → /stock/sortie/
- Inventaire            → /stock/inventaire/
- Rapport PDF           → /rapports/journalier/ → bouton PDF
- Rapport mensuel       → /rapports/mensuel/
- Ajouter dépense       → /depenses/ajouter/
- Messagerie            → /messagerie/envoyer/
- Mot de passe          → /profil/ onglet Sécurité
- Catégories            → /produits/ onglet Catégories

Tu peux : donner les chiffres en temps réel, guider l'utilisation, signaler alertes stock.
Tu ne modifies PAS les données — tu guides vers la bonne page."""


@login_required
@csrf_exempt
def chatbot_init(request):
  try:
    donnees = get_donnees_boutique(request.user)
    role_label = (
        'Administrateur' if request.user.role == 'ADMIN' else 'Gestionnaire'
    )
    alertes_liste = (
        '\n'.join([f"  • {p}" for p in donnees['produits_alerte']])
        if donnees['produits_alerte']
        else '  • Aucun produit en alerte ✅'
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

💬 Posez-moi vos questions sur les chiffres, l'utilisation de l'app ou les alertes stock ! 😊"""

    return JsonResponse({
        'reponse': salutation,
        'donnees': donnees,
        'message_initial': True,
    })

  except Exception as e:
    return JsonResponse({
        'reponse': (
            'Bonjour ! Je suis IBRA, votre assistant. Comment puis-je vous'
            ' aider ?'
        )
    }, status=200)


@login_required
@csrf_exempt
def chatbot_query(request):
  if request.method != 'POST':
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

  try:
    body = json.loads(request.body)
    message = body.get('message', '').strip()
    historique = body.get('historique', [])

    if not message:
      return JsonResponse({'error': 'Message vide'}, status=400)

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
      return JsonResponse({
          'reponse': (
              "❌ Clé API Groq non configurée. Ajoutez GROQ_API_KEY dans les"
              ' variables d\'environnement.'
          )
      }, status=200)

    donnees = get_donnees_boutique(request.user)
    client = Groq(api_key=api_key)

    # Construire les messages avec le prompt système
    messages = [{
        'role': 'system',
        'content': construire_prompt_systeme(request.user, donnees),
    }]

    # Ajouter l'historique
    for msg in historique[-10:]:
      role = 'user' if msg['role'] == 'user' else 'assistant'
      messages.append({'role': role, 'content': msg['content']})

    # Ajouter le nouveau message
    messages.append({'role': 'user', 'content': message})

    # Appel Groq avec le nom de modèle officiel
    response = client.chat.completions.create(
        model=os.getenv('GROQ_MODEL', 'llama3-70b-8192'),
        max_tokens=500,
        messages=messages,
    )

    reponse_text = response.choices[0].message.content

    return JsonResponse({
        'reponse': reponse_text,
        'donnees': donnees,
    })

  except Exception as e:
    err = str(e)
    if '401' in err or 'authentication' in err.lower():
      msg = '❌ Clé API invalide. Vérifiez GROQ_API_KEY.'
    elif '429' in err:
      msg = '⚠️ Trop de requêtes. Réessayez dans quelques secondes.'
    else:
      msg = f'⚠️ Erreur : {err}'
    return JsonResponse({'reponse': msg}, status=200)