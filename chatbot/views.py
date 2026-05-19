import os
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from openai import OpenAI


def get_donnees_boutique(user):
    """Récupère les données en temps réel selon le rôle."""
    from ventes.models import Vente
    from depenses.models import Depense
    from produits.models import Produit
    from django.db.models import Sum
    from datetime import timedelta

    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)
    semaine_derniere_debut = aujourd_hui - timedelta(days=7)
    semaine_avant_derniere = semaine_derniere_debut - timedelta(days=7)

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

        ca_semaine_actuelle = Vente.objects.filter(
            date_vente__date__gte=semaine_derniere_debut, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        ca_semaine_derniere = Vente.objects.filter(
            date_vente__date__gte=semaine_avant_derniere,
            date_vente__date__lt=semaine_derniere_debut,
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        depenses_mois = Depense.objects.filter(
            date_depense__gte=debut_mois
        ).aggregate(t=Sum('montant'))['t'] or 0

        nb_ventes = Vente.objects.filter(
            date_vente__date__gte=debut_mois, annulee=False
        ).count()

        # Dernière vente et dernière clôture
        derniere_vente = Vente.objects.filter(annulee=False).order_by('-date_vente').first()
        derniere_vente_info = f"{derniere_vente.gestionnaire.get_full_name()} le {derniere_vente.date_vente.strftime('%H:%M')}" if derniere_vente else "Aucune"

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

        ca_semaine_actuelle = Vente.objects.filter(
            gestionnaire=user,
            date_vente__date__gte=semaine_derniere_debut,
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0

        ca_semaine_derniere = Vente.objects.filter(
            gestionnaire=user,
            date_vente__date__gte=semaine_avant_derniere,
            date_vente__date__lt=semaine_derniere_debut,
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

        derniere_vente = Vente.objects.filter(gestionnaire=user, annulee=False).order_by('-date_vente').first()
        derniere_vente_info = f"{derniere_vente.date_vente.strftime('%H:%M')}" if derniere_vente else "Aucune"

    nb_produits_alerte = len(produits_alerte)
    details_alertes = [f"{p.nom} ({p.quantite_stock} restant(s))" for p in produits_alerte[:10]]

    # Comparaison semaine
    evolution_semaine = "↗️ EN HAUSSE" if ca_semaine_actuelle > ca_semaine_derniere else "↘️ EN BAISSE" if ca_semaine_actuelle < ca_semaine_derniere else "→ STABLE"

    return {
        'ca_jour': float(ca_jour),
        'ca_mois': float(ca_mois),
        'ca_semaine_actuelle': float(ca_semaine_actuelle),
        'ca_semaine_derniere': float(ca_semaine_derniere),
        'evolution_semaine': evolution_semaine,
        'depenses_mois': float(depenses_mois),
        'benefice_net': float(ca_mois) - float(depenses_mois),
        'nb_ventes_mois': nb_ventes,
        'nb_produits_alerte': nb_produits_alerte,
        'produits_alerte': details_alertes,
        'derniere_vente': derniere_vente_info,
        'date': aujourd_hui.strftime('%d/%m/%Y'),
    }


def construire_prompt_systeme(user, donnees):
    """Construit le prompt système personnalisé avec assistance technique et métier."""
    role_label = "Administrateur" if user.role == 'ADMIN' else "Gestionnaire"
    
    assistance_technique = """
# 🔧 ASSISTANCE TECHNIQUE (Support de l'application)
Quand l'utilisateur demande comment utiliser une fonctionnalité, réponds avec des étapes précises :

**Modifier le prix d'un article :**
1. Allez dans le menu /stock/ 
2. Cherchez l'article dans la liste
3. Cliquez sur le bouton modifier (icône crayon) à côté de l'article
4. Changez le prix de vente ou prix d'achat
5. Cliquez sur "Enregistrer"

**Ajouter un produit :**
1. Allez à /produits/ajouter/
2. Remplissez : Nom, Catégorie, Prix achat, Prix vente, Quantité initiale
3. Optionnel : Ajoutez une image et réglez le seuil d'alerte
4. Cliquez "Enregistrer"

**Enregistrer une vente :**
1. Allez à /ventes/enregistrer/
2. Cherchez l'article par nom ou catégorie
3. Entrez la quantité vendue et prix de vente
4. Cliquez "Valider" - le stock se mettra à jour automatiquement

**Approvisionner le stock :**
1. Allez à /stock/entree/
2. Sélectionnez l'article et la quantité reçue
3. Entrez le prix d'achat unitaire si différent
4. Cliquez "Enregistrer"

**Voir l'historique des ventes :**
1. Allez à /ventes/
2. Utilisez les filtres : Par date, article, gestionnaire
3. Cliquez sur une vente pour voir les détails

**Faire l'inventaire :**
1. Allez à /stock/inventaire/
2. Comptez les articles en magasin
3. Entrez la quantité réelle pour chaque article
4. Le système corrigera automatiquement
"""

    analyse_metier = f"""
# 📊 ASSISTANT MÉTIER ET STATISTIQUES
DONNÉES EN TEMPS RÉEL DE LA BOUTIQUE ({donnees['date']}) :

**Performance financière :**
- 💰 CA aujourd'hui : {donnees['ca_jour']:,.0f} FCFA
- 📈 CA ce mois : {donnees['ca_mois']:,.0f} FCFA
- 📊 CA semaine actuelle : {donnees['ca_semaine_actuelle']:,.0f} FCFA {donnees['evolution_semaine']}
- 📉 CA semaine dernière : {donnees['ca_semaine_derniere']:,.0f} FCFA
- 💸 Dépenses ce mois : {donnees['depenses_mois']:,.0f} FCFA
- 💵 Bénéfice net : {donnees['benefice_net']:,.0f} FCFA
- 📦 Nombre de ventes ce mois : {donnees['nb_ventes_mois']}

**Alertes stock ⚠️ :**
- 🚨 Produits en alerte : {donnees['nb_produits_alerte']}
{chr(10).join([f"  • {produit}" for produit in donnees['produits_alerte']]) if donnees['produits_alerte'] else "  • Aucun produit en alerte - stock OK!"}

**Questions métier que tu dois pouvoir répondre :**
- "Quel est le CA d'aujourd'hui ?" → Réponds avec les chiffres en temps réel
- "Est-ce qu'on a mieux vendu cette semaine ?" → Compare semaine actuelle vs dernière
- "Quels articles sont en rupture de stock ?" → Liste les produits en alerte
- "Combien de ventes on a ce mois ?" → Donne le nombre total
- "Quel est notre bénéfice net ?" → Calcule CA - Dépenses

**Comparaisons :**
- Evolution semaine : {donnees['evolution_semaine']}
- Tendance à identifier et commenter
"""

    # Guide d'utilisation complet
    guide_complet = """
# 📋 GUIDE D'UTILISATION COMPLET

## Menu Principal
- **/login/** : Connexion
- **/dashboard/** : Tableau de bord avec graphiques
- **/admin-dashboard/** : Vue administrateur globale

## Gestion des produits
- **/produits/** : Liste produits + onglet Catégories
- **/produits/ajouter/** : Créer un nouveau produit
- **/produits/<id>/modifier/** : Éditer un produit

## Ventes
- **/ventes/enregistrer/** : Enregistrer une vente (déduit automatiquement du stock)
- **/ventes/** : Historique complet avec filtres
- **/rapports/journalier/** : Rapport du jour (export PDF)

## Stock
- **/stock/** : État du stock avec alertes
- **/stock/entree/** : Enregistrer un approvisionnement
- **/stock/historique/** : Historique des mouvements
- **/stock/inventaire/** : Faire un inventaire complet

## Dépenses et finances
- **/depenses/ajouter/** : Enregistrer une dépense
- **/rapports/mensuel/** : Rapport mensuel complet

## Communication
- **/messagerie/** : Messagerie interne entre gestionnaire et admin
- **/profil/** : Profil personnel et changement mot de passe
"""

    return f"""Tu es IBRA, l'assistant intelligent de la boutique IBRAFRIK Decor 🤖

Tu t'adresses à {user.get_full_name() or user.username}, qui est **{role_label}**.

{assistance_technique}

{analyse_metier}

{guide_complet}

## 🎯 RÈGLES DE COMPORTEMENT :
1. Réponds TOUJOURS en français
2. Sois concis, professionnel et chaleureux
3. Pour les données chiffrées, utilise les DONNÉES EN TEMPS RÉEL fournies
4. Quand tu n'es pas sûr, demande plus de précisions
5. Si l'utilisateur te demande de modifier des données, explique comment utiliser l'application pour le faire
6. Donne des suggestions proactives : "Je vois que vous avez {{nb_produits_alerte}} produits en alerte, voulez-vous les approvisionner ?"
7. Ne partage JAMAIS les informations d'un autre utilisateur
"""


@login_required
@csrf_exempt
def chatbot_init(request):
    """Initialise le chatbot avec un message de salutation et infos du site."""
    try:
        # Données boutique en temps réel
        donnees = get_donnees_boutique(request.user)
        role_label = "Administrateur" if request.user.role == 'ADMIN' else "Gestionnaire"
        
        # Message de salutation initial enrichi
        salutation = f"""Bonjour {request.user.get_full_name() or request.user.username}! 👋

Je suis IBRA, votre assistant intelligent pour la gestion de la boutique IBRAFRIK Decor.

Vous êtes connecté en tant que **{role_label}**.

📊 **Situation actuelle** ({donnees['date']}) :
- CA aujourd'hui : {donnees['ca_jour']:,.0f} FCFA
- CA ce mois : {donnees['ca_mois']:,.0f} FCFA  
- CA semaine : {donnees['ca_semaine_actuelle']:,.0f} FCFA {donnees['evolution_semaine']}
- Bénéfice net : {donnees['benefice_net']:,.0f} FCFA
- Nombre de ventes ce mois : {donnees['nb_ventes_mois']}

⚠️ **Alertes importantes** :
- 🚨 Produits en alerte stock : {donnees['nb_produits_alerte']}
{chr(10).join([f"  • {produit}" for produit in donnees['produits_alerte']]) if donnees['produits_alerte'] else "  • Aucun produit en alerte - stock OK!"}

💬 **Comment puis-je vous aider ?**
- 📈 "Quel est notre CA d'aujourd'hui ?" → Je vous donne les chiffres en direct
- 📊 "Est-ce qu'on a mieux vendu cette semaine ?" → Je compare avec la semaine dernière
- ⚠️ "Quels articles sont en rupture de stock ?" → Je vous liste les produits en alerte
- 🛒 "Comment enregistrer une vente ?" → Je vous guide étape par étape
- 📝 "Comment ajouter un produit ?" → Je vous explique la procédure
- 💾 "Comment faire un inventaire ?" → Instructions complètes
- 🔍 "Quelle est l'historique des ventes ?" → Je récupère les données

Posez-moi vos questions en langage naturel - je suis là pour vous aider! 😊
"""
        
        return JsonResponse({
            'reponse': salutation,
            'donnees': donnees,
            'message_initial': True
        })
    
    except Exception as e:
        return JsonResponse({
            'reponse': f"Désolé, une erreur s'est produite : {str(e)}"
        }, status=200)


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
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return JsonResponse({'error': 'Clé API OpenAI non configurée'}, status=500)

        # Données boutique en temps réel
        donnees = get_donnees_boutique(request.user)

        # Client OpenAI
        client = OpenAI(api_key=api_key)

        # Construire l'historique des messages
        messages = [
            {
                'role': 'system',
                'content': construire_prompt_systeme(request.user, donnees)
            }
        ]
        
        for msg in historique[-10:]:  # 10 derniers messages max
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

        # Ajouter le nouveau message
        messages.append({
            'role': 'user',
            'content': message
        })

        # ✅ Appel à OpenAI avec gpt-4o-mini (stable et performant)
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )

        reponse_text = response.choices[0].message.content or "Je n'ai pas pu générer une réponse."

        return JsonResponse({
            'reponse': reponse_text,
            'donnees': donnees,
        })

    except Exception as e:
        return JsonResponse({
            'reponse': f"Désolé, une erreur s'est produite : {str(e)}"
        }, status=200)