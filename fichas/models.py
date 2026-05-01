from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    tipo = models.CharField(max_length=20, choices=[
        ('mestre', 'Mestre'),
        ('player', 'Player')
    ], default='player')


class Campanha(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    mestre = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campanhas_como_mestre')
    members = models.ManyToManyField(User, blank=True, related_name='campanhas_como_player')
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Ficha(models.Model):
    dono = models.ForeignKey(User, on_delete=models.CASCADE)
    campanha = models.ForeignKey(Campanha, on_delete=models.SET_NULL, null=True, blank=True, related_name='fichas')

    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    classe = models.CharField(max_length=100, blank=True)

    idade = models.CharField(max_length=20, blank=True)
    altura = models.CharField(max_length=20, blank=True)
    peso = models.CharField(max_length=20, blank=True)
    raca = models.CharField(max_length=50, blank=True)

    nivel = models.IntegerField(default=1)

    forca = models.IntegerField(default=0)
    destreza = models.IntegerField(default=0)
    constituicao = models.IntegerField(default=0)
    inteligencia = models.IntegerField(default=0)
    sabedoria = models.IntegerField(default=0)
    carisma = models.IntegerField(default=0)

    bonus_forca = models.IntegerField(default=0)
    bonus_destreza = models.IntegerField(default=0)
    bonus_constituicao = models.IntegerField(default=0)
    bonus_inteligencia = models.IntegerField(default=0)
    bonus_sabedoria = models.IntegerField(default=0)
    bonus_carisma = models.IntegerField(default=0)

    vida_max = models.IntegerField(default=0)
    energia_max = models.IntegerField(default=0)
    sanidade_max = models.IntegerField(default=0)

    vida = models.IntegerField(default=0)
    energia = models.IntegerField(default=0)
    sanidade = models.IntegerField(default=0)
    armadura = models.IntegerField(default=0)
    defesa = models.IntegerField(default=0)

    formula_vida = models.CharField(max_length=200, blank=True, default='')
    formula_energia = models.CharField(max_length=200, blank=True, default='')
    formula_sanidade = models.CharField(max_length=200, blank=True, default='')
    formula_defesa = models.CharField(max_length=200, blank=True, default='')

    atk1 = models.CharField(max_length=100, blank=True)
    pts1 = models.CharField(max_length=20, blank=True)
    dano1 = models.CharField(max_length=100, blank=True)
    atk2 = models.CharField(max_length=100, blank=True)
    pts2 = models.CharField(max_length=20, blank=True)
    dano2 = models.CharField(max_length=100, blank=True)
    atk3 = models.CharField(max_length=100, blank=True)
    pts3 = models.CharField(max_length=20, blank=True)
    dano3 = models.CharField(max_length=100, blank=True)

    habilidades = models.TextField(blank=True)
    pericias = models.TextField(blank=True)
    vantagens = models.TextField(blank=True)
    poderes = models.TextField(blank=True)

    foto = models.ImageField(upload_to='fichas/', blank=True, null=True)

    carga_max = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def peso_atual(self):
        return round(sum(float(i.peso) * i.quantidade for i in self.itens.all()), 2)

    def __str__(self):
        return self.nome


class ItemInventario(models.Model):
    CATEGORIAS = [
        ('arma', 'Arma'),
        ('armadura', 'Armadura'),
        ('consumivel', 'Consumível'),
        ('ferramenta', 'Ferramenta'),
        ('misc', 'Misc'),
    ]
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='itens')
    nome = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='misc')
    quantidade = models.IntegerField(default=1)
    peso = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    dano = models.CharField(max_length=50, blank=True)
    bonus_ataque = models.IntegerField(default=0)
    bonus_defesa = models.IntegerField(default=0)
    descricao = models.TextField(blank=True)
    modificacoes = models.TextField(blank=True)
    maldicoes = models.TextField(blank=True)

    def peso_total(self):
        return round(float(self.peso) * self.quantidade, 2)

    def __str__(self):
        return f'{self.nome} (x{self.quantidade})'


class Criatura(models.Model):
    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE, related_name='criaturas', null=True, blank=True)
    criada_por = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    foto = models.ImageField(upload_to='criaturas/', blank=True, null=True)
    nivel = models.IntegerField(default=1)
    valor_desafio = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    forca = models.IntegerField(default=0)
    destreza = models.IntegerField(default=0)
    constituicao = models.IntegerField(default=0)
    inteligencia = models.IntegerField(default=0)
    sabedoria = models.IntegerField(default=0)
    carisma = models.IntegerField(default=0)
    vida_max = models.IntegerField(default=0)
    vida = models.IntegerField(default=0)
    armadura = models.IntegerField(default=0)
    defesa = models.IntegerField(default=0)
    atk1 = models.CharField(max_length=100, blank=True)
    dano1 = models.CharField(max_length=50, blank=True)
    atk2 = models.CharField(max_length=100, blank=True)
    dano2 = models.CharField(max_length=50, blank=True)
    habilidades = models.TextField(blank=True)

    def __str__(self):
        return self.nome


class CombateSession(models.Model):
    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE, related_name='combates')
    nome = models.CharField(max_length=100, default='Combate')
    ativo = models.BooleanField(default=True)
    turno_atual = models.IntegerField(default=0)
    rodada = models.IntegerField(default=1)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nome} — {self.campanha.nome}'


class ParticipanteCombate(models.Model):
    combate = models.ForeignKey(CombateSession, on_delete=models.CASCADE, related_name='participantes')
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, null=True, blank=True)
    criatura = models.ForeignKey(Criatura, on_delete=models.CASCADE, null=True, blank=True)
    nome_override = models.CharField(max_length=100, blank=True)
    iniciativa = models.IntegerField(default=0)
    vida_atual = models.IntegerField(default=0)
    vida_max = models.IntegerField(default=0)
    derrotado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-iniciativa']

    @property
    def nome_display(self):
        if self.nome_override:
            return self.nome_override
        if self.ficha:
            return self.ficha.nome
        if self.criatura:
            return self.criatura.nome
        return '???'

    @property
    def eh_player(self):
        return self.ficha is not None

    def __str__(self):
        return self.nome_display


class Rolagem(models.Model):
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='rolagens')
    jogador = models.ForeignKey(User, on_delete=models.CASCADE)
    expressao = models.CharField(max_length=100)
    resultado = models.JSONField()
    contexto = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']