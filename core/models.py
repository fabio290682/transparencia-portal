import uuid

from django.core.validators import FileExtensionValidator
from django.db import models


def generate_uuid():
	return str(uuid.uuid4())


class UnidadeGestora(models.Model):
	id = models.CharField(primary_key=True, max_length=36, default=generate_uuid, editable=False)
	codigo = models.CharField(max_length=32, unique=True)
	nome = models.CharField(max_length=128)
	sigla = models.CharField(max_length=16)

	def __str__(self):
		return self.nome


class Despesa(models.Model):
	CATEGORIA_CHOICES = [
		("PESSOAL", "Pessoal"),
		("CUSTEIO", "Custeio"),
		("INVESTIMENTO", "Investimento"),
		("TRANSFERENCIA", "Transferência"),
	]
	id = models.CharField(primary_key=True, max_length=36, default=generate_uuid, editable=False)
	codigo = models.CharField(max_length=32)
	descricao = models.CharField(max_length=128)
	categoria = models.CharField(max_length=16, choices=CATEGORIA_CHOICES)
	dotacao = models.DecimalField(max_digits=15, decimal_places=2)
	empenhado = models.DecimalField(max_digits=15, decimal_places=2)
	liquidado = models.DecimalField(max_digits=15, decimal_places=2)
	pago = models.DecimalField(max_digits=15, decimal_places=2)
	exercicio = models.IntegerField()
	unidade = models.ForeignKey(UnidadeGestora, related_name="despesas", on_delete=models.CASCADE)

	def __str__(self):
		return self.descricao


class Licitacao(models.Model):
	MODALIDADE_CHOICES = [
		("PREGAO_ELETRONICO", "Pregão Eletrônico"),
		("TOMADA_PRECOS", "Tomada de Preços"),
		("CONCORRENCIA", "Concorrência"),
		("DISPENSA", "Dispensa"),
		("INEXIGIBILIDADE", "Inexigibilidade"),
	]
	STATUS_CHOICES = [
		("PUBLICADA", "Publicada"),
		("EM_ANDAMENTO", "Em Andamento"),
		("HOMOLOGADA", "Homologada"),
		("CANCELADA", "Cancelada"),
		("SUSPENSA", "Suspensa"),
		("REVOGADA", "Revogada"),
	]
	id = models.CharField(primary_key=True, max_length=36, default=generate_uuid, editable=False)
	numero = models.CharField(max_length=32, unique=True)
	objeto = models.CharField(max_length=256)
	modalidade = models.CharField(max_length=24, choices=MODALIDADE_CHOICES)
	status = models.CharField(max_length=16, choices=STATUS_CHOICES)
	valor_estimado = models.DecimalField(max_digits=15, decimal_places=2)
	data_abertura = models.DateTimeField()
	unidade = models.ForeignKey(UnidadeGestora, related_name="licitacoes", on_delete=models.CASCADE)

	def __str__(self):
		return self.numero


class Servidor(models.Model):
	VINCULO_CHOICES = [
		("EFETIVO", "Efetivo"),
		("COMISSIONADO", "Comissionado"),
		("CLT", "CLT"),
		("TEMPORARIO", "Temporário"),
		("ESTAGIARIO", "Estagiário"),
	]
	id = models.CharField(primary_key=True, max_length=36, default=generate_uuid, editable=False)
	matricula = models.CharField(max_length=32, unique=True)
	nome = models.CharField(max_length=128)
	cargo = models.CharField(max_length=64)
	vinculo = models.CharField(max_length=16, choices=VINCULO_CHOICES)
	remuneracao_bruta = models.DecimalField(max_digits=12, decimal_places=2)
	descontos = models.DecimalField(max_digits=12, decimal_places=2)
	competencia = models.CharField(max_length=16)
	unidade = models.ForeignKey(UnidadeGestora, related_name="servidores", on_delete=models.CASCADE)

	def __str__(self):
		return self.nome


class EsicPedido(models.Model):
	TIPO_CHOICES = [
		("PEDIDO_ACESSO", "Pedido de Acesso à Informação"),
		("RECLAMACAO", "Reclamação"),
		("DENUNCIA", "Denúncia"),
		("SUGESTAO", "Sugestão"),
		("ELOGIO", "Elogio"),
	]
	STATUS_CHOICES = [
		("ABERTO", "Aberto"),
		("EM_ANALISE", "Em Análise"),
		("RESPONDIDO", "Respondido"),
		("INDEFERIDO", "Indeferido"),
		("ARQUIVADO", "Arquivado"),
	]
	id = models.CharField(primary_key=True, max_length=36, default=generate_uuid, editable=False)
	protocolo = models.CharField(max_length=32, unique=True)
	tipo = models.CharField(max_length=16, choices=TIPO_CHOICES)
	descricao = models.TextField()
	status = models.CharField(max_length=16, choices=STATUS_CHOICES)
	email = models.EmailField(blank=True, null=True)
	anexo = models.FileField(upload_to='esic_anexos/', blank=True, null=True)
	prazo = models.DateTimeField()
	resposta = models.TextField(blank=True, null=True)
	unidade = models.ForeignKey(UnidadeGestora, related_name="pedidos", on_delete=models.CASCADE)

	def __str__(self):
		return self.protocolo


class PortalInformacao(models.Model):
	SECAO_CHOICES = [
		("FINANCEIROS", "Relatórios Financeiros"),
		("PRESTACAO", "Prestação de Contas"),
		("CONTRATACOES", "Contratações"),
		("POLITICAS", "Políticas e Regulamentos"),
	]

	id = models.CharField(primary_key=True, max_length=36, default=generate_uuid, editable=False)
	secao = models.CharField(max_length=20, choices=SECAO_CHOICES)
	titulo = models.CharField(max_length=180)
	descricao = models.TextField()
	link = models.URLField(blank=True, null=True)
	arquivo = models.FileField(
		upload_to='portal_documentos/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(allowed_extensions=['pdf', 'xls', 'xlsx'])],
	)
	ordem = models.PositiveIntegerField(default=0)
	ativo = models.BooleanField(default=True)
	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["secao", "ordem", "titulo"]

	def __str__(self):
		return f"{self.get_secao_display()} - {self.titulo}"

	@property
	def possui_arquivo(self):
		return bool(self.arquivo)

	@property
	def url_documento(self):
		if self.arquivo:
			return self.arquivo.url
		return self.link
