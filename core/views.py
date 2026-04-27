import logging
import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.validators import validate_email
from django.db.utils import IntegrityError, OperationalError, ProgrammingError
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Despesa,
    EsicPedido,
    Licitacao,
    PortalInformacao,
    Projeto,
    Servidor,
    UnidadeGestora,
)
from .serializers import (
    DespesaSerializer,
    EsicPedidoSerializer,
    LicitacaoSerializer,
    ServidorSerializer,
    UnidadeGestoraSerializer,
)
from .throttles import RegisterAnonThrottle

logger = logging.getLogger(__name__)


def _as_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _seed_portal_info_if_needed() -> None:
    default_seed = not (getattr(settings, "IS_VERCEL", False) and not settings.DEBUG)
    if not _as_bool(os.getenv("DJANGO_AUTO_SEED_ON_BOOT"), default=default_seed):
        return

    try:
        if PortalInformacao.objects.exists():
            return
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Falha ao checar dados existentes de portal: %s", exc)
        return

    try:
        call_command("seed_portal_info", verbosity=0)
        logger.info("Seed de portal executado automaticamente.")
    except (CommandError, OperationalError, ProgrammingError) as exc:
        logger.exception("Falha ao executar seed_portal_info automaticamente: %s", exc)


def _safe_infos_ativos():
    try:
        return list(PortalInformacao.objects.filter(ativo=True))
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Falha ao carregar PortalInformacao: %s", exc)
        return []


def _safe_infos_por_secao():
    infos = _safe_infos_ativos()

    return {
        "FINANCEIROS": [info for info in infos if info.secao == "FINANCEIROS"],
        "PRESTACAO": [info for info in infos if info.secao == "PRESTACAO"],
        "CONTRATACOES": [info for info in infos if info.secao == "CONTRATACOES"],
        "POLITICAS": [info for info in infos if info.secao == "POLITICAS"],
    }


def _safe_projetos():
    try:
        return list(Projeto.objects.filter(ativo=True).order_by("status", "ordem", "titulo"))
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Falha ao carregar Projetos: %s", exc)
        return []


def _safe_termos_fomento(projetos=None):
    projetos = _safe_projetos() if projetos is None else projetos

    def _matches_termo(projeto):
        campos = [
            projeto.titulo,
            projeto.subtitulo,
            projeto.instrumento,
            projeto.nome_projeto,
        ]
        termos = ("termo de fomento", "termo de patrocin")
        return any(termo in (campo or "").lower() for campo in campos for termo in termos)

    return [projeto for projeto in projetos if _matches_termo(projeto)]

TIPO_ESIC_MAP = {
    "Acesso à Informação": "PEDIDO_ACESSO",
    "Acesso a informação": "PEDIDO_ACESSO",
    "Acesso Ã  InformaÃ§Ã£o": "PEDIDO_ACESSO",
    "Acesso a Informacao": "PEDIDO_ACESSO",
    "PEDIDO_ACESSO": "PEDIDO_ACESSO",
    "Reclamação": "RECLAMACAO",
    "ReclamaÃ§Ã£o": "RECLAMACAO",
    "Reclamacao": "RECLAMACAO",
    "RECLAMACAO": "RECLAMACAO",
    "Denúncia": "DENUNCIA",
    "DenÃºncia": "DENUNCIA",
    "Denuncia": "DENUNCIA",
    "DENUNCIA": "DENUNCIA",
    "Sugestão": "SUGESTAO",
    "SugestÃ£o": "SUGESTAO",
    "Sugestao": "SUGESTAO",
    "SUGESTAO": "SUGESTAO",
    "Elogio": "ELOGIO",
    "ELOGIO": "ELOGIO",
}



def _get_or_create_default_unidade():
    unidade = UnidadeGestora.objects.first()
    if unidade:
        return unidade

    return UnidadeGestora.objects.create(
        id=str(uuid.uuid4()),
        codigo="UG-PADRAO",
        nome="Unidade Gestora Padrao",
        sigla="UGP",
    )



def _generate_protocolo():
    while True:
        suffix = str(uuid.uuid4().int)[:8]
        protocolo = f"ESIC-{timezone.now():%Y%m%d}-{suffix}"
        if not EsicPedido.objects.filter(protocolo=protocolo).exists():
            return protocolo


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterAnonThrottle])
def register_user(request):
    if not settings.ALLOW_PUBLIC_REGISTRATION:
        return Response(
            {"error": "Cadastro publico desabilitado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    email = (request.data.get("email") or "").strip()

    if not username or not password:
        return Response(
            {"error": "Usuario e senha sao obrigatorios."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 8:
        return Response(
            {"error": "A senha deve ter pelo menos 8 caracteres."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Usuario ja existe."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        User.objects.create_user(username=username, password=password, email=email)
    except IntegrityError:
        return Response(
            {"error": "Usuario ja existe."},
            status=status.HTTP_409_CONFLICT,
        )
    except (OperationalError, ProgrammingError) as exc:
        logger.exception("Falha de banco em register_user: %s", exc)
        return Response(
            {"error": "Servico indisponivel no momento. Tente novamente em instantes."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response({"message": "Usuario criado com sucesso."}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def submit_esic_request(request):
    tipo_input = (request.data.get("tipo") or "").strip()
    descricao = (request.data.get("descricao") or "").strip()
    email = (request.data.get("email") or "").strip()
    nome = (request.data.get("nome") or "").strip()
    setor = (request.data.get("setor") or "").strip()
    formato_resposta = (request.data.get("formato_resposta") or "").strip()
    anexo = request.FILES.get("anexo")

    if not descricao:
        return Response(
            {"error": "Descricao do pedido e obrigatoria."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tipo = TIPO_ESIC_MAP.get(tipo_input, "PEDIDO_ACESSO")

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return Response({"error": "Email invalido."}, status=status.HTTP_400_BAD_REQUEST)

    if anexo:
        if anexo.size > 3 * 1024 * 1024:
            return Response(
                {"error": "O anexo deve ter no maximo 3MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not anexo.name.lower().endswith(".pdf"):
            return Response(
                {"error": "Apenas arquivos PDF sao permitidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        unidade = _get_or_create_default_unidade()
        prazo = timezone.now() + timedelta(days=20)
        protocolo = _generate_protocolo()
    except (OperationalError, ProgrammingError) as exc:
        logger.exception("Falha de banco ao preparar ESIC: %s", exc)
        return Response(
            {"error": "Servico indisponivel no momento. Tente novamente em instantes."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    descricao_expandida = descricao
    extras = []
    if nome:
        extras.append(f"Nome: {nome}")
    if setor and setor != "Selecione...":
        extras.append(f"Setor: {setor}")
    if formato_resposta:
        extras.append(f"Formato de resposta: {formato_resposta}")
    if extras:
        descricao_expandida = f"{descricao}\n\n" + "\n".join(extras)

    try:
        EsicPedido.objects.create(
            id=str(uuid.uuid4()),
            protocolo=protocolo,
            tipo=tipo,
            descricao=descricao_expandida,
            status="ABERTO",
            email=email or "",
            anexo=anexo,
            prazo=prazo,
            unidade=unidade,
        )
    except IntegrityError:
        protocolo = _generate_protocolo()
        try:
            EsicPedido.objects.create(
                id=str(uuid.uuid4()),
                protocolo=protocolo,
                tipo=tipo,
                descricao=descricao_expandida,
                status="ABERTO",
                email=email or "",
                anexo=anexo,
                prazo=prazo,
                unidade=unidade,
            )
        except IntegrityError as exc:
            logger.exception("Falha persistente ao gravar pedido e-SIC: %s", exc)
            return Response(
                {"error": "Nao foi possivel registrar o pedido agora. Tente novamente."},
                status=status.HTTP_409_CONFLICT,
            )
    except (OperationalError, ProgrammingError) as exc:
        logger.exception("Falha ao gravar pedido e-SIC: %s", exc)
        return Response(
            {"error": "Servico indisponivel no momento. Tente novamente em instantes."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response(
        {"message": "Solicitacao registrada com sucesso.", "protocolo": protocolo},
        status=status.HTTP_201_CREATED,
    )



def home(request):
    _seed_portal_info_if_needed()
    infos_por_secao = _safe_infos_por_secao()
    projetos = _safe_projetos()
    termos_fomento = _safe_termos_fomento(projetos)
    return render(
        request,
        "portal_transparencia.html",
        {
            "infos_por_secao": infos_por_secao,
            "projetos": projetos,
            "termos_fomento": termos_fomento,
        },
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_portal_info(request):
    _seed_portal_info_if_needed()
    infos = sorted(
        _safe_infos_ativos(),
        key=lambda info: (info.secao, info.ordem, info.titulo),
    )

    payload = {
        "FINANCEIROS": [],
        "PRESTACAO": [],
        "CONTRATACOES": [],
        "POLITICAS": [],
    }

    for info in infos:
        payload[info.secao].append(
            {
                "id": info.id,
                "secao": info.secao,
                "titulo": info.titulo,
                "descricao": info.descricao,
                "ordem": info.ordem,
                "possui_arquivo": info.possui_arquivo,
                "url_documento": info.url_documento,
                "atualizado_em": info.atualizado_em.isoformat(),
            },
        )

    return Response({"items": payload}, status=status.HTTP_200_OK)


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


