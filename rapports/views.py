from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from ventes.models import Vente
from depenses.models import Depense
import io


@login_required
def rapport_journalier(request):
    date_str    = request.GET.get('date', timezone.now().date().isoformat())
    from datetime import date as dt
    date_cible  = dt.fromisoformat(date_str)

    ventes   = Vente.objects.filter(
        gestionnaire=request.user,
        date_vente__date=date_cible,
        annulee=False
    ).select_related('produit')

    depenses = Depense.objects.filter(
        gestionnaire=request.user,
        date_depense=date_cible
    )

    ca_total  = ventes.aggregate(t=Sum('montant_total'))['t'] or 0
    dep_total = depenses.aggregate(t=Sum('montant'))['t'] or 0
    solde     = ca_total - dep_total

    return render(request, 'rapports/journalier.html', {
        'date':      date_cible,
        'ventes':    ventes,
        'depenses':  depenses,
        'ca_total':  ca_total,
        'dep_total': dep_total,
        'solde':     solde,
    })


@login_required
def rapport_mensuel(request):
    aujourd_hui = timezone.now().date()
    mois        = int(request.GET.get('mois', aujourd_hui.month))
    annee       = int(request.GET.get('annee', aujourd_hui.year))

    ventes   = Vente.objects.filter(
        gestionnaire=request.user,
        date_vente__month=mois,
        date_vente__year=annee,
        annulee=False
    ).select_related('produit')

    depenses = Depense.objects.filter(
        gestionnaire=request.user,
        date_depense__month=mois,
        date_depense__year=annee
    )

    ca_total  = ventes.aggregate(t=Sum('montant_total'))['t'] or 0
    dep_total = depenses.aggregate(t=Sum('montant'))['t'] or 0
    benefice  = ca_total - dep_total

    # Top produits du mois
    top = ventes.values('produit__nom').annotate(
        qte=Sum('quantite'),
        ca=Sum('montant_total')
    ).order_by('-ca')[:5]

    return render(request, 'rapports/mensuel.html', {
        'mois':      mois,
        'annee':     annee,
        'ventes':    ventes,
        'depenses':  depenses,
        'ca_total':  ca_total,
        'dep_total': dep_total,
        'benefice':  benefice,
        'top':       top,
        'mois_list': range(1, 13),
    })


@login_required
def exporter_pdf_journalier(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm

    date_str   = request.GET.get('date', timezone.now().date().isoformat())
    from datetime import date as dt
    date_cible = dt.fromisoformat(date_str)

    ventes   = Vente.objects.filter(
        gestionnaire=request.user,
        date_vente__date=date_cible,
        annulee=False
    ).select_related('produit')

    depenses = Depense.objects.filter(
        gestionnaire=request.user,
        date_depense=date_cible
    )

    ca_total  = ventes.aggregate(t=Sum('montant_total'))['t'] or 0
    dep_total = depenses.aggregate(t=Sum('montant'))['t'] or 0
    solde     = ca_total - dep_total

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                               topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # Titre
    story.append(Paragraph(
        f"Rapport Journalier — {date_cible.strftime('%d/%m/%Y')}",
        styles['Title']
    ))
    story.append(Paragraph(
        f"Gestionnaire : {request.user.get_full_name() or request.user.username}",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.5*cm))

    # Résumé
    resume = [
        ['Chiffre d\'affaires', f'{ca_total:,.0f} FCFA'],
        ['Total dépenses',      f'{dep_total:,.0f} FCFA'],
        ['Solde net',           f'{solde:,.0f} FCFA'],
    ]
    t = Table(resume, colWidths=[8*cm, 6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('FONTNAME',   (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 11),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1),
         [colors.white, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # Ventes
    story.append(Paragraph('Détail des Ventes', styles['Heading2']))
    if ventes:
        data = [['Produit', 'Qté', 'Prix unit.', 'Total', 'Client']]
        for v in ventes:
            data.append([
                v.produit.nom,
                str(v.quantite),
                f'{v.prix_unitaire:,.0f}',
                f'{v.montant_total:,.0f}',
                v.client or '—',
            ])
        tv = Table(data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 4*cm])
        tv.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.lightblue]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(tv)
    else:
        story.append(Paragraph('Aucune vente ce jour.', styles['Normal']))

    story.append(Spacer(1, 0.5*cm))

    # Dépenses
    story.append(Paragraph('Détail des Dépenses', styles['Heading2']))
    if depenses:
        data2 = [['Libellé', 'Catégorie', 'Montant']]
        for d in depenses:
            data2.append([d.libelle, d.categorie_depense, f'{d.montant:,.0f} FCFA'])
        td = Table(data2, colWidths=[7*cm, 5*cm, 5*cm])
        td.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.lightyellow]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(td)
    else:
        story.append(Paragraph('Aucune dépense ce jour.', styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="rapport_{date_cible}.pdf"'
    )
    return response