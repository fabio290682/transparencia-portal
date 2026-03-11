"""Arquivo de configuração do app `core`."""

import uuid
from typing import ClassVar

from django.core.validators import FileExtensionValidator
from django.db import models


def generate_uuid() -> str:
    """Gera um UUID aleatório para ser usado como chave primária."""
    return str(uuid.uuid4())


class UnidadeGestora(models.Model):
    """Representa uma unidade gestora no sistema."""

    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=generate_uuid,
        editable=False,
    )
    codigo = models.CharField(max_length=32, unique=True)
    nome = models.CharField(max_length=128)
    sigla = models.CharField(max_length=16)

    def __str__(self) -> str:
        """Representação em string do objeto."""
        return self.nome



class Despesa(models.Model):
    """Representa uma despesa no sistema."""

    CATEGORIA_CHOICES: "ClassVar" = [
        ("PESSOAL", "Pessoal"),
        ("CUSTEIO", "Custeio"),
        ("INVESTIMENTO", "Investimento"),
        ("TRANSFERENCIA", "Transferência"),
    ]
    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=generate_uuid,
        editable=False,
    )
    codigo = models.CharField(max_length=32)
    descricao = models.CharField(max_length=128)
    categoria = models.CharField(max_length=16, choices=CATEGORIA_CHOICES)
    dotacao = models.DecimalField(max_digits=15, decimal_places=2)
    empenhado = models.DecimalField(max_digits=15, decimal_places=2)
    liquidado = models.DecimalField(max_digits=15, decimal_places=2)
    pago = models.DecimalField(max_digits=15, decimal_places=2)
    exercicio = models.IntegerField()
    unidade = models.ForeignKey(
        UnidadeGestora,
        related_name="despesas",
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        """Representação em string do objeto."""
        return self.descricao


class Licitacao(models.Model):
    """Representa uma licitação no sistema."""

    MODALIDADE_CHOICES: "ClassVar" = [
        ("PREGAO_ELETRONICO", "Pregão Eletrônico"),
        ("TOMADA_PRECOS", "Tomada de Preços"),
        ("CONCORRENCIA", "Concorrência"),
        ("DISPENSA", "Dispensa"),
        ("INEXIGIBILIDADE", "Inexigibilidade"),
    ]
    STATUS_CHOICES: "ClassVar" = [
        ("PUBLICADA", "Publicada"),
        ("EM_ANDAMENTO", "Em Andamento"),
        ("HOMOLOGADA", "Homologada"),
        ("CANCELADA", "Cancelada"),
        ("SUSPENSA", "Suspensa"),
        ("REVOGADA", "Revogada"),
    ]
    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=generate_uuid,
        editable=False,
    )
    numero = models.CharField(max_length=32, unique=True)
    objeto = models.CharField(max_length=256)
    modalidade = models.CharField(max_length=24, choices=MODALIDADE_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    valor_estimado = models.DecimalField(max_digits=15, decimal_places=2)
    data_abertura = models.DateTimeField()
    unidade = models.ForeignKey(
        UnidadeGestora,
        related_name="licitacoes",
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        """Representação em string do objeto."""
        return self.numero

class Servidor(models.Model):
    """Representa um servidor no sistema."""

    VINCULO_CHOICES: "ClassVar" = [
        ("EFETIVO", "Efetivo"),
        ("COMISSIONADO", "Comissionado"),
        ("CLT", "CLT"),
        ("TEMPORARIO", "Temporário"),
        ("ESTAGIARIO", "Estagiário"),
    ]
    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=generate_uuid,
        editable=False,
    )
    matricula = models.CharField(max_length=32, unique=True)
    nome = models.CharField(max_length=128)
    cargo = models.CharField(max_length=64)
    vinculo = models.CharField(max_length=16, choices=VINCULO_CHOICES)
    remuneracao_bruta = models.DecimalField(max_digits=12, decimal_places=2)
    descontos = models.DecimalField(max_digits=12, decimal_places=2)
    competencia = models.CharField(max_length=16)
    unidade = models.ForeignKey(
        UnidadeGestora,
        related_name="servidores",
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        """Representação em string do objeto."""
        return self.nome


class EsicPedido(models.Model):
    """Representa um pedido de informação (e-SIC) no sistema."""

    TIPO_CHOICES: "ClassVar" = [
        ("PEDIDO_ACESSO", "Pedido de Acesso à Informação"),
        ("RECLAMACAO", "Reclamação"),
        ("DENUNCIA", "Denúncia"),
        ("SUGESTAO", "Sugestão"),
        ("ELOGIO", "Elogio"),
    ]
    STATUS_CHOICES: "ClassVar" = [
        ("ABERTO", "Aberto"),
        ("EM_ANALISE", "Em Análise"),
        ("RESPONDIDO", "Respondido"),
        ("INDEFERIDO", "Indeferido"),
        ("ARQUIVADO", "Arquivado"),
    ]
    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=generate_uuid,
        editable=False,
    )
    protocolo = models.CharField(max_length=32, unique=True)
    tipo = models.CharField(max_length=16, choices=TIPO_CHOICES)
    descricao = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    email = models.EmailField(blank=True, default="")
    anexo = models.FileField(upload_to="esic_anexos/", blank=True, null=True)
    prazo = models.DateTimeField()
    resposta = models.TextField(blank=True, default="")
    unidade = models.ForeignKey(
        UnidadeGestora,
        related_name="pedidos",
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        """Representação em string do objeto."""
        return self.protocolo


class PortalInformacao(models.Model):
    """Representa uma informação publicada no portal da transparência."""

    SECAO_CHOICES: "ClassVar" = [
        ("FINANCEIROS", "Relatórios Financeiros"),
        ("PRESTACAO", "Prestação de Contas"),
        ("CONTRATACOES", "Contratações"),
        ("POLITICAS", "Políticas e Regulamentos"),
    ]

    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=generate_uuid,
        editable=False,
    )
    secao = models.CharField(max_length=20, choices=SECAO_CHOICES)
    titulo = models.CharField(max_length=180)
    descricao = models.TextField()
    link = models.URLField(blank=True, default="")
    arquivo = models.FileField(
        upload_to="portal_documentos/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "xls", "xlsx"]),
        ],
    )
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for PortalInformacao."""

        ordering: "ClassVar" = ["secao", "ordem", "titulo"]

    def __str__(self) -> str:
        """Representação em string do objeto."""
        return f"{self.get_secao_display()} - {self.titulo}"

    @property
    def possui_arquivo(self) -> bool:
        """Retorna True se o item possui um arquivo anexado."""
        return bool(self.arquivo)

    @property
    def url_documento(self) -> str:
        """Retorna a URL do documento (arquivo ou link)."""
        if self.arquivo:
            return self.arquivo.url
        return self.link


class Projeto(models.Model):
    """Representa um projeto no sistema."""

    STATUS_CHOICES: "ClassVar" = [
        ("EM_ANDAMENTO", "Em Andamento"),
        ("FINALIZADO", "Finalizado"),
    ]

    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=generate_uuid,
        editable=False,
    )
    titulo = models.CharField(max_length=255)
    subtitulo = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    icone = models.CharField(max_length=8, default="📌")
    valor = models.CharField(max_length=40)
    instrumento = models.CharField(max_length=255)
    recurso_financeiro = models.CharField(max_length=64, blank=True)
    fonte_recurso_estadual = models.CharField(max_length=64, blank=True)
    fonte_recurso_federal = models.CharField(max_length=64, blank=True)
    autoria_emenda = models.TextField(blank=True)
    nome_projeto = models.CharField(max_length=255, blank=True)
    valor_repassado = models.CharField(max_length=64, blank=True)
    valor_global = models.CharField(max_length=64, blank=True)
    objeto = models.TextField(blank=True)
    data_inicio = models.CharField(max_length=64, blank=True)
    data_finalizacao = models.CharField(max_length=64, blank=True)
    justificativa = models.TextField(blank=True)
    dados_orcamentarios = models.TextField(blank=True)
    arquivo = models.FileField(
        upload_to="projeto_documentos/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "xls", "xlsx"]),
        ],
    )
    documento_link = models.URLField(blank=True, default="")
    documento_label = models.CharField(max_length=200, blank=True)
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for Projeto."""

        ordering: "ClassVar" = ["ordem", "-criado_em"]

    def __str__(self) -> str:
        """Representação em string do objeto."""
        return self.titulo

    @property
    def status_label(self) -> str:
        """Retorna o label do status do projeto."""
        return self.get_status_display()

    @property
    def data_status(self) -> str:
        """Retorna o status do projeto para uso em atributos de dados."""
        return self.get_status_display()

    @property
    def possui_arquivo(self) -> bool:
        """Retorna True se o projeto possui um arquivo anexado."""
        return bool(self.arquivo)

    @property
    def url_documento(self) -> str:
        """Retorna a URL do documento (arquivo ou link externo)."""
        if self.arquivo:
            return self.arquivo.url
        return self.documento_link
