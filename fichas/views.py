from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Ficha, Campanha, Rolagem, ItemInventario, Criatura, CombateSession, ParticipanteCombate
import random
import re
import json


# ─────────────────────────────
# DASHBOARD
# ─────────────────────────────
@login_required
def dashboard(request):
    if request.user.tipo == 'mestre':
        fichas = Ficha.objects.all()
        campanhas = Campanha.objects.filter(mestre=request.user)
        rolagens = Rolagem.objects.select_related('ficha', 'jogador').all()[:50]
    else:
        fichas = Ficha.objects.filter(dono=request.user)
        campanhas = (
            Campanha.objects.filter(members=request.user) |
            Campanha.objects.filter(mestre=request.user)
        ).distinct()
        rolagens = None

    return render(request, 'dashboard.html', {
        'fichas': fichas,
        'campanhas': campanhas,
        'rolagens': rolagens,
    })


# ─────────────────────────────
# FICHA
# ─────────────────────────────
@login_required
def criar_ficha(request):
    ficha = Ficha.objects.create(dono=request.user, nome='Novo Personagem')
    return redirect(f'/ficha/{ficha.id}/')


@login_required
def editar_ficha(request, id):
    ficha = get_object_or_404(Ficha, id=id)

    if request.user.tipo != 'mestre' and ficha.dono != request.user:
        return redirect('/')

    if request.method == 'POST':
        _atualizar_ficha(ficha, request)
        if request.FILES.get('foto'):
            ficha.foto = request.FILES['foto']
        ficha.save()
        if 'voltar' in request.POST:
            return redirect('/')

    rolagens = ficha.rolagens.all()[:30]
    itens = ficha.itens.all()
    campanhas_disponiveis = Campanha.objects.all()

    return render(request, 'ficha.html', {
        'ficha': ficha,
        'rolagens': rolagens,
        'itens': itens,
        'campanhas_disponiveis': campanhas_disponiveis,
    })


def _atualizar_ficha(ficha, request):
    P = request.POST.get

    ficha.nome = P('nome') or ficha.nome
    ficha.descricao = P('descricao', '')
    ficha.classe = P('classe', '')
    ficha.idade = P('idade', '')
    ficha.altura = P('altura', '')
    ficha.peso = P('peso', '')
    ficha.raca = P('raca', '')
    ficha.nivel = int(P('nivel') or 1)

    for attr in ('forca', 'destreza', 'constituicao', 'inteligencia', 'sabedoria', 'carisma'):
        setattr(ficha, attr, int(P(attr) or 0))
        setattr(ficha, f'bonus_{attr}', int(P(f'bonus_{attr}') or 0))

    ficha.vida = int(P('vida') or 0)
    ficha.vida_max = int(P('vida_max') or 0)
    ficha.energia = int(P('energia') or 0)
    ficha.energia_max = int(P('energia_max') or 0)
    ficha.sanidade = int(P('sanidade') or 0)
    ficha.sanidade_max = int(P('sanidade_max') or 0)
    ficha.armadura = int(P('armadura') or 0)
    ficha.defesa = int(P('defesa') or 0)

    ficha.formula_vida = P('formula_vida', '')
    ficha.formula_energia = P('formula_energia', '')
    ficha.formula_sanidade = P('formula_sanidade', '')
    ficha.formula_defesa = P('formula_defesa', '')

    for i in ('1', '2', '3'):
        setattr(ficha, f'atk{i}', P(f'atk{i}', ''))
        setattr(ficha, f'pts{i}', P(f'pts{i}', ''))
        setattr(ficha, f'dano{i}', P(f'dano{i}', ''))

    ficha.habilidades = P('habilidades', '')
    ficha.pericias = P('pericias', '')
    ficha.vantagens = P('vantagens', '')
    ficha.poderes = P('poderes', '')

    try:
        ficha.carga_max = float(P('carga_max') or 0)
    except ValueError:
        ficha.carga_max = 0

    campanha_id = P('campanha')
    ficha.campanha_id = campanha_id if campanha_id and campanha_id != '0' else None


@login_required
def autosave_ficha(request, id):
    if request.method != 'POST':
        return JsonResponse({'status': 'invalido'}, status=400)

    ficha = get_object_or_404(Ficha, id=id)
    if request.user.tipo != 'mestre' and ficha.dono != request.user:
        return JsonResponse({'status': 'erro'}, status=403)

    P = request.POST.get
    ficha.nome = P('nome') or ficha.nome
    ficha.descricao = P('descricao', ficha.descricao)
    ficha.vida = int(P('vida') or ficha.vida)
    ficha.vida_max = int(P('vida_max') or ficha.vida_max)
    ficha.energia = int(P('energia') or ficha.energia)
    ficha.energia_max = int(P('energia_max') or ficha.energia_max)
    ficha.sanidade = int(P('sanidade') or ficha.sanidade)
    ficha.sanidade_max = int(P('sanidade_max') or ficha.sanidade_max)
    ficha.defesa = int(P('defesa') or ficha.defesa)
    ficha.save()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def deletar_ficha(request, id):
    ficha = get_object_or_404(Ficha, id=id)
    if request.user.tipo != 'mestre' and ficha.dono != request.user:
        return redirect('/')
    ficha.delete()
    return redirect('/')


# ─────────────────────────────
# DADOS
# ─────────────────────────────
@login_required
@require_POST
def rolar_dados(request, id):
    ficha = get_object_or_404(Ficha, id=id)
    if ficha.dono != request.user and request.user.tipo != 'mestre':
        return JsonResponse({'status': 'erro', 'msg': 'Sem permissão'}, status=403)

    expressao = request.POST.get('expressao', '').strip().lower()
    contexto = request.POST.get('contexto', '').strip()

    padrao = re.fullmatch(r'(\d+)d(\d+)([+-]\d+)?', expressao.replace(' ', ''))
    if not padrao:
        return JsonResponse({'status': 'erro', 'msg': 'Use: 2d20, 1d6+3'}, status=400)

    qtd = int(padrao.group(1))
    lados = int(padrao.group(2))
    modificador = int(padrao.group(3)) if padrao.group(3) else 0

    if qtd < 1 or qtd > 20 or lados < 2 or lados > 100:
        return JsonResponse({'status': 'erro', 'msg': 'Máx 20 dados, máx d100'}, status=400)

    valores = [random.randint(1, lados) for _ in range(qtd)]
    total = sum(valores) + modificador

    rolagem = Rolagem.objects.create(
        ficha=ficha, jogador=request.user,
        expressao=expressao,
        resultado={'dados': valores, 'modificador': modificador, 'total': total},
        contexto=contexto,
    )

    return JsonResponse({
        'status': 'ok',
        'expressao': expressao,
        'contexto': contexto,
        'dados': valores,
        'modificador': modificador,
        'total': total,
        'jogador': request.user.username,
        'personagem': ficha.nome,
        'id': rolagem.id,
    })


# ─────────────────────────────
# INVENTÁRIO
# ─────────────────────────────
@login_required
@require_POST
def adicionar_item(request, ficha_id):
    ficha = get_object_or_404(Ficha, id=ficha_id)
    if request.user.tipo != 'mestre' and ficha.dono != request.user:
        return JsonResponse({'status': 'erro'}, status=403)

    item = ItemInventario.objects.create(
        ficha=ficha,
        nome=request.POST.get('nome', 'Item'),
        categoria=request.POST.get('categoria', 'misc'),
        quantidade=int(request.POST.get('quantidade') or 1),
        peso=float(request.POST.get('peso') or 0),
        dano=request.POST.get('dano', ''),
        bonus_ataque=int(request.POST.get('bonus_ataque') or 0),
        bonus_defesa=int(request.POST.get('bonus_defesa') or 0),
        descricao=request.POST.get('descricao', ''),
        modificacoes=request.POST.get('modificacoes', ''),
        maldicoes=request.POST.get('maldicoes', ''),
    )

    return JsonResponse({
        'status': 'ok',
        'id': item.id,
        'nome': item.nome,
        'categoria': item.categoria,
        'quantidade': item.quantidade,
        'peso': float(item.peso),
        'peso_total': item.peso_total(),
        'dano': item.dano,
        'bonus_ataque': item.bonus_ataque,
        'bonus_defesa': item.bonus_defesa,
        'descricao': item.descricao,
        'modificacoes': item.modificacoes,
        'maldicoes': item.maldicoes,
        'peso_atual_ficha': ficha.peso_atual(),
    })


@login_required
@require_POST
def editar_item(request, item_id):
    item = get_object_or_404(ItemInventario, id=item_id)
    ficha = item.ficha
    if request.user.tipo != 'mestre' and ficha.dono != request.user:
        return JsonResponse({'status': 'erro'}, status=403)

    item.nome = request.POST.get('nome', item.nome)
    item.categoria = request.POST.get('categoria', item.categoria)
    item.quantidade = int(request.POST.get('quantidade') or item.quantidade)
    item.peso = float(request.POST.get('peso') or item.peso)
    item.dano = request.POST.get('dano', item.dano)
    item.bonus_ataque = int(request.POST.get('bonus_ataque') or 0)
    item.bonus_defesa = int(request.POST.get('bonus_defesa') or 0)
    item.descricao = request.POST.get('descricao', item.descricao)
    item.modificacoes = request.POST.get('modificacoes', item.modificacoes)
    item.maldicoes = request.POST.get('maldicoes', item.maldicoes)
    item.save()

    return JsonResponse({
        'status': 'ok',
        'peso_total': item.peso_total(),
        'peso_atual_ficha': ficha.peso_atual(),
    })


@login_required
@require_POST
def deletar_item(request, item_id):
    item = get_object_or_404(ItemInventario, id=item_id)
    ficha = item.ficha
    if request.user.tipo != 'mestre' and ficha.dono != request.user:
        return JsonResponse({'status': 'erro'}, status=403)
    item.delete()
    return JsonResponse({'status': 'ok', 'peso_atual_ficha': ficha.peso_atual()})


# ─────────────────────────────
# CAMPANHAS
# ─────────────────────────────
@login_required
def criar_campanha(request):
    if request.user.tipo != 'mestre':
        return redirect('/')
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        if nome:
            campanha = Campanha.objects.create(nome=nome, descricao=descricao, mestre=request.user)
            return redirect(f'/campanha/{campanha.id}/')
    return render(request, 'criar_campanha.html')


@login_required
def ver_campanha(request, id):
    campanha = get_object_or_404(Campanha, id=id)
    fichas = campanha.fichas.select_related('dono').all()
    criaturas = campanha.criaturas.all()
    combate_ativo = campanha.combates.filter(ativo=True).first()
    ja_membro = request.user in campanha.members.all()
    eh_mestre = campanha.mestre == request.user

    return render(request, 'campanha.html', {
        'campanha': campanha,
        'fichas': fichas,
        'criaturas': criaturas,
        'combate_ativo': combate_ativo,
        'ja_membro': ja_membro,
        'eh_mestre': eh_mestre,
    })


@login_required
@require_POST
def entrar_campanha(request, id):
    campanha = get_object_or_404(Campanha, id=id)
    if request.user.tipo == 'player':
        campanha.members.add(request.user)
    return redirect(f'/campanha/{id}/')


@login_required
@require_POST
def sair_campanha(request, id):
    campanha = get_object_or_404(Campanha, id=id)
    campanha.members.remove(request.user)
    Ficha.objects.filter(dono=request.user, campanha=campanha).update(campanha=None)
    return redirect('/')


@login_required
@require_POST
def deletar_campanha(request, id):
    campanha = get_object_or_404(Campanha, id=id)
    if campanha.mestre != request.user:
        return redirect('/')
    campanha.delete()
    return redirect('/')


# ─────────────────────────────
# ESCUDO
# ─────────────────────────────
@login_required
def escudo_api(request, id):
    campanha = get_object_or_404(Campanha, id=id)
    if campanha.mestre != request.user:
        return JsonResponse({'status': 'erro'}, status=403)

    fichas = campanha.fichas.select_related('dono').all()
    data = [{
        'id': f.id,
        'nome': f.nome,
        'dono': f.dono.username,
        'classe': f.classe,
        'nivel': f.nivel,
        'vida': f.vida,
        'vida_max': f.vida_max,
        'energia': f.energia,
        'energia_max': f.energia_max,
        'sanidade': f.sanidade,
        'sanidade_max': f.sanidade_max,
        'armadura': f.armadura,
        'defesa': f.defesa,
        'foto': f.foto.url if f.foto else None,
    } for f in fichas]

    return JsonResponse({'fichas': data})


# ─────────────────────────────
# BESTIÁRIO
# ─────────────────────────────
@login_required
def criar_criatura(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.mestre != request.user:
        return redirect('/')

    if request.method == 'POST':
        criatura = Criatura.objects.create(
            campanha=campanha,
            criada_por=request.user,
            nome=request.POST.get('nome', 'Criatura'),
            descricao=request.POST.get('descricao', ''),
            nivel=int(request.POST.get('nivel') or 1),
            valor_desafio=float(request.POST.get('valor_desafio') or 1),
            forca=int(request.POST.get('forca') or 0),
            destreza=int(request.POST.get('destreza') or 0),
            constituicao=int(request.POST.get('constituicao') or 0),
            inteligencia=int(request.POST.get('inteligencia') or 0),
            sabedoria=int(request.POST.get('sabedoria') or 0),
            carisma=int(request.POST.get('carisma') or 0),
            vida_max=int(request.POST.get('vida_max') or 0),
            vida=int(request.POST.get('vida_max') or 0),
            armadura=int(request.POST.get('armadura') or 0),
            defesa=int(request.POST.get('defesa') or 0),
            atk1=request.POST.get('atk1', ''),
            dano1=request.POST.get('dano1', ''),
            atk2=request.POST.get('atk2', ''),
            dano2=request.POST.get('dano2', ''),
            habilidades=request.POST.get('habilidades', ''),
        )
        if request.FILES.get('foto'):
            criatura.foto = request.FILES['foto']
            criatura.save()
        return redirect(f'/campanha/{campanha_id}/')

    return render(request, 'criar_criatura.html', {'campanha': campanha})


@login_required
@require_POST
def deletar_criatura(request, criatura_id):
    criatura = get_object_or_404(Criatura, id=criatura_id)
    campanha_id = criatura.campanha_id
    if criatura.criada_por != request.user:
        return redirect('/')
    criatura.delete()
    return redirect(f'/campanha/{campanha_id}/')


# ─────────────────────────────
# COMBATE
# ─────────────────────────────
@login_required
@require_POST
def iniciar_combate(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.mestre != request.user:
        return JsonResponse({'status': 'erro'}, status=403)

    # Encerra combate anterior se houver
    campanha.combates.filter(ativo=True).update(ativo=False)

    combate = CombateSession.objects.create(
        campanha=campanha,
        nome=request.POST.get('nome', 'Combate'),
    )

    # Adiciona fichas da campanha
    fichas_ids = request.POST.getlist('fichas[]')
    for fid in fichas_ids:
        try:
            ficha = Ficha.objects.get(id=fid, campanha=campanha)
            ParticipanteCombate.objects.create(
                combate=combate,
                ficha=ficha,
                iniciativa=int(request.POST.get(f'iniciativa_{fid}') or 0),
                vida_atual=ficha.vida,
                vida_max=ficha.vida_max or ficha.vida,
            )
        except Ficha.DoesNotExist:
            pass

    # Adiciona criaturas
    criaturas_ids = request.POST.getlist('criaturas[]')
    for cid in criaturas_ids:
        try:
            criatura = Criatura.objects.get(id=cid, campanha=campanha)
            qtd = int(request.POST.get(f'qtd_{cid}') or 1)
            for n in range(qtd):
                nome_override = criatura.nome if qtd == 1 else f'{criatura.nome} {n+1}'
                ParticipanteCombate.objects.create(
                    combate=combate,
                    criatura=criatura,
                    nome_override=nome_override,
                    iniciativa=int(request.POST.get(f'ini_criatura_{cid}') or random.randint(1, 20)),
                    vida_atual=criatura.vida_max,
                    vida_max=criatura.vida_max,
                )
        except Criatura.DoesNotExist:
            pass

    return JsonResponse({'status': 'ok', 'combate_id': combate.id})


@login_required
def combate_api(request, combate_id):
    combate = get_object_or_404(CombateSession, id=combate_id)
    campanha = combate.campanha
    if campanha.mestre != request.user:
        return JsonResponse({'status': 'erro'}, status=403)

    participantes = list(combate.participantes.all())
    vivos = [p for p in participantes if not p.derrotado]
    turno_atual = combate.turno_atual % len(vivos) if vivos else 0

    data = {
        'id': combate.id,
        'nome': combate.nome,
        'rodada': combate.rodada,
        'turno_atual': combate.turno_atual,
        'ativo': combate.ativo,
        'participantes': [{
            'id': p.id,
            'nome': p.nome_display,
            'eh_player': p.eh_player,
            'iniciativa': p.iniciativa,
            'vida_atual': p.vida_atual,
            'vida_max': p.vida_max,
            'derrotado': p.derrotado,
            'ativo': (not p.derrotado and vivos and vivos[turno_atual].id == p.id),
        } for p in participantes],
    }

    # Valor de desafio total
    vd_total = sum(
        float(p.criatura.valor_desafio) for p in participantes if p.criatura
    )
    data['valor_desafio_total'] = round(vd_total, 2)

    return JsonResponse(data)


@login_required
@require_POST
def acao_combate(request, combate_id):
    combate = get_object_or_404(CombateSession, id=combate_id)
    if combate.campanha.mestre != request.user:
        return JsonResponse({'status': 'erro'}, status=403)

    acao = request.POST.get('acao')

    if acao == 'proximo_turno':
        participantes = list(combate.participantes.filter(derrotado=False))
        if participantes:
            combate.turno_atual = (combate.turno_atual + 1) % len(participantes)
            if combate.turno_atual == 0:
                combate.rodada += 1
            combate.save()

    elif acao == 'dano':
        pid = request.POST.get('participante_id')
        valor = int(request.POST.get('valor') or 0)
        p = get_object_or_404(ParticipanteCombate, id=pid, combate=combate)
        p.vida_atual = max(0, p.vida_atual - valor)
        if p.vida_atual == 0:
            p.derrotado = True
        p.save()
        # Sincroniza com ficha real
        if p.ficha:
            p.ficha.vida = p.vida_atual
            p.ficha.save()

    elif acao == 'cura':
        pid = request.POST.get('participante_id')
        valor = int(request.POST.get('valor') or 0)
        p = get_object_or_404(ParticipanteCombate, id=pid, combate=combate)
        p.vida_atual = min(p.vida_max, p.vida_atual + valor)
        p.derrotado = False
        p.save()
        if p.ficha:
            p.ficha.vida = p.vida_atual
            p.ficha.save()

    elif acao == 'encerrar':
        combate.ativo = False
        combate.save()

    return JsonResponse({'status': 'ok'})