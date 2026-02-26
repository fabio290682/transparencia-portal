import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import UnidadeGestora, Despesa, Licitacao, Servidor, EsicPedido, PortalInformacao
from .serializers import (
    UnidadeGestoraSerializer,
    DespesaSerializer,
    LicitacaoSerializer,
    ServidorSerializer,
    EsicPedidoSerializer,
)


TIPO_ESIC_MAP = {
    'Acesso à Informação': 'PEDIDO_ACESSO',
    'Acesso a Informacao': 'PEDIDO_ACESSO',
    'PEDIDO_ACESSO': 'PEDIDO_ACESSO',
    'Reclamação': 'RECLAMACAO',
    'Reclamacao': 'RECLAMACAO',
    'RECLAMACAO': 'RECLAMACAO',
    'Denúncia': 'DENUNCIA',
    'Denuncia': 'DENUNCIA',
    'DENUNCIA': 'DENUNCIA',
    'Sugestão': 'SUGESTAO',
    'Sugestao': 'SUGESTAO',
    'SUGESTAO': 'SUGESTAO',
    'Elogio': 'ELOGIO',
    'ELOGIO': 'ELOGIO',
}



def _get_or_create_default_unidade():
    unidade = UnidadeGestora.objects.first()
    if unidade:
        return unidade

    return UnidadeGestora.objects.create(
        id=str(uuid.uuid4()),
        codigo='UG-PADRAO',
        nome='Unidade Gestora Padrao',
        sigla='UGP',
    )



def _generate_protocolo():
    while True:
        suffix = str(uuid.uuid4().int)[:8]
        protocolo = f'ESIC-{timezone.now():%Y%m%d}-{suffix}'
        if not EsicPedido.objects.filter(protocolo=protocolo).exists():
            return protocolo


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    email = (request.data.get('email') or '').strip()

    if not username or not password:
        return Response(
            {'error': 'Usuario e senha sao obrigatorios.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 8:
        return Response(
            {'error': 'A senha deve ter pelo menos 8 caracteres.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Usuario ja existe.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    User.objects.create_user(username=username, password=password, email=email)
    return Response({'message': 'Usuario criado com sucesso.'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_esic_request(request):
    tipo_input = (request.data.get('tipo') or '').strip()
    descricao = (request.data.get('descricao') or '').strip()
    email = (request.data.get('email') or '').strip()
    nome = (request.data.get('nome') or '').strip()
    setor = (request.data.get('setor') or '').strip()
    formato_resposta = (request.data.get('formato_resposta') or '').strip()
    anexo = request.FILES.get('anexo')

    if not descricao:
        return Response(
            {'error': 'Descricao do pedido e obrigatoria.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tipo = TIPO_ESIC_MAP.get(tipo_input, 'PEDIDO_ACESSO')

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Email invalido.'}, status=status.HTTP_400_BAD_REQUEST)

    if anexo:
        if anexo.size > 3 * 1024 * 1024:
            return Response(
                {'error': 'O anexo deve ter no maximo 3MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not anexo.name.lower().endswith('.pdf'):
            return Response(
                {'error': 'Apenas arquivos PDF sao permitidos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    unidade = _get_or_create_default_unidade()
    prazo = timezone.now() + timedelta(days=20)
    protocolo = _generate_protocolo()

    descricao_expandida = descricao
    extras = []
    if nome:
        extras.append(f'Nome: {nome}')
    if setor and setor != 'Selecione...':
        extras.append(f'Setor: {setor}')
    if formato_resposta:
        extras.append(f'Formato de resposta: {formato_resposta}')
    if extras:
        descricao_expandida = f'{descricao}\n\n' + '\n'.join(extras)

    EsicPedido.objects.create(
        id=str(uuid.uuid4()),
        protocolo=protocolo,
        tipo=tipo,
        descricao=descricao_expandida,
        status='ABERTO',
        email=email or None,
        anexo=anexo,
        prazo=prazo,
        unidade=unidade,
    )

    return Response(
        {'message': 'Solicitacao registrada com sucesso.', 'protocolo': protocolo},
        status=status.HTTP_201_CREATED,
    )



def home(request):
    infos = PortalInformacao.objects.filter(ativo=True)
    infos_por_secao = {
        'FINANCEIROS': infos.filter(secao='FINANCEIROS'),
        'PRESTACAO': infos.filter(secao='PRESTACAO'),
        'CONTRATACOES': infos.filter(secao='CONTRATACOES'),
        'POLITICAS': infos.filter(secao='POLITICAS'),
    }
    return render(request, 'portal_transparencia.html', {'infos_por_secao': infos_por_secao})


class UnidadeGestoraViewSet(viewsets.ModelViewSet):
    queryset = UnidadeGestora.objects.all()
    serializer_class = UnidadeGestoraSerializer
    permission_classes = [IsAuthenticated]


class DespesaViewSet(viewsets.ModelViewSet):
    queryset = Despesa.objects.all()
    serializer_class = DespesaSerializer
    permission_classes = [IsAuthenticated]


class LicitacaoViewSet(viewsets.ModelViewSet):
    queryset = Licitacao.objects.all()
    serializer_class = LicitacaoSerializer
    permission_classes = [IsAuthenticated]


class ServidorViewSet(viewsets.ModelViewSet):
    queryset = Servidor.objects.all()
    serializer_class = ServidorSerializer
    permission_classes = [IsAuthenticated]


class EsicPedidoViewSet(viewsets.ModelViewSet):
    queryset = EsicPedido.objects.all()
    serializer_class = EsicPedidoSerializer
    permission_classes = [IsAuthenticated]
