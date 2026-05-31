import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Livre
from .forms import LivreForm
from . import chatbot


# ── Livres CRUD ───────────────────────────────────────────────────────────────

def livre_list(request):
    query  = request.GET.get('q', '').strip()
    livres = Livre.objects.all()
    if query:
        livres = livres.filter(
            Q(titre__icontains=query) |
            Q(auteur__icontains=query) |
            Q(id__exact=query if query.isdigit() else -1)
        )
    return render(request, 'livres_temp/livre_list.html',
                  {'livres': livres, 'query': query})


def livre_create(request):
    if request.method == 'POST':
        form = LivreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Livre ajouté avec succès.')
            return redirect('livre_list')
    else:
        form = LivreForm()
    return render(request, 'livres_temp/livre_form.html',
                  {'form': form, 'titre_page': 'Ajouter un Livre'})


def livre_update(request, pk):
    livre = get_object_or_404(Livre, pk=pk)
    if request.method == 'POST':
        form = LivreForm(request.POST, instance=livre)
        if form.is_valid():
            form.save()
            messages.success(request, 'Livre modifié avec succès.')
            return redirect('livre_list')
    else:
        form = LivreForm(instance=livre)
    return render(request, 'livres_temp/livre_form.html',
                  {'form': form, 'titre_page': f'Modifier : {livre.titre}', 'livre': livre})


def livre_delete(request, pk):
    livre = get_object_or_404(Livre, pk=pk)
    if request.method == 'POST':
        livre.delete()
        messages.success(request, 'Livre supprimé.')
        return redirect('livre_list')
    return render(request, 'livres_temp/livre_confirm_delete.html', {'livre': livre})


# ── Chatbot ───────────────────────────────────────────────────────────────────

def chatbot_page(request):
    return render(request, 'livres_temp/chatbot.html')


def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        data    = json.loads(request.body)
        message = data.get('message', '').strip()
        if not message:
            return JsonResponse({'error': 'Message vide'}, status=400)

        history = request.session.get('chat_history', [])
        livres  = list(Livre.objects.values())

        reply, updated_history = chatbot.ask_chatbot(message, livres, history)
        request.session['chat_history'] = updated_history
        request.session.modified = True

        return JsonResponse({'reply': reply})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


def chatbot_clear(request):
    request.session['chat_history'] = []
    return JsonResponse({'status': 'cleared'})
