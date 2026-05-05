from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Message
from .forms import MessageForm
from accounts.models import Utilisateur


@login_required
def inbox(request):
    messages_recus = Message.objects.filter(
        destinataire=request.user
    ).select_related('expediteur').order_by('-date_envoi')

    # Marquer comme lus
    messages_recus.filter(lu=False).update(lu=True)

    return render(request, 'messagerie/inbox.html', {
        'messages_recus': messages_recus,
    })


@login_required
def envoyer(request):
    form = MessageForm(request.POST or None, user=request.user)

    if form.is_valid():
        msg = form.save(commit=False)
        msg.expediteur = request.user
        msg.save()
        messages.success(request, 'Message envoyé avec succès.')
        return redirect('messagerie:inbox')

    return render(request, 'messagerie/envoyer.html', {'form': form})


@login_required
def message_detail(request, pk):
    message = get_object_or_404(
        Message, pk=pk, destinataire=request.user
    )
    return render(request, 'messagerie/detail.html', {'message': message})


@login_required
def sent(request):
    messages_envoyes = Message.objects.filter(
        expediteur=request.user
    ).select_related('destinataire').order_by('-date_envoi')

    return render(request, 'messagerie/sent.html', {
        'messages_envoyes': messages_envoyes,
    })