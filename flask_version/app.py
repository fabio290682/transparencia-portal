from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = os.getenv("VERCEL") == "1"
RUNTIME_DIR = Path("/tmp") if IS_VERCEL else BASE_DIR

MEDIA_DIR = RUNTIME_DIR / "media"
UPLOAD_DIR = MEDIA_DIR / "esic_anexos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static",
)

DB_PATH = RUNTIME_DIR / "flask_portal.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024

db = SQLAlchemy(app)


class UnidadeGestora(db.Model):
    __tablename__ = "unidade_gestora"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo = db.Column(db.String(32), unique=True, nullable=False)
    nome = db.Column(db.String(128), nullable=False)
    sigla = db.Column(db.String(16), nullable=False)


class EsicPedido(db.Model):
    __tablename__ = "esic_pedido"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    protocolo = db.Column(db.String(32), unique=True, nullable=False)
    tipo = db.Column(db.String(16), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="ABERTO")
    email = db.Column(db.String(255), nullable=True)
    anexo = db.Column(db.String(255), nullable=True)
    prazo = db.Column(db.DateTime, nullable=False)
    resposta = db.Column(db.Text, nullable=True)
    unidade_id = db.Column(db.String(36), db.ForeignKey("unidade_gestora.id"), nullable=False)


class PortalInformacao(db.Model):
    __tablename__ = "portal_informacao"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    secao = db.Column(db.String(20), nullable=False)
    titulo = db.Column(db.String(180), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500), nullable=True)
    arquivo = db.Column(db.String(500), nullable=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def possui_arquivo(self) -> bool:
        return bool(self.arquivo)

    @property
    def url_documento(self) -> str | None:
        if self.arquivo:
            return self.arquivo
        return self.link


TIPO_ESIC_MAP = {
    "Acesso à Informação": "PEDIDO_ACESSO",
    "Acesso a Informacao": "PEDIDO_ACESSO",
    "PEDIDO_ACESSO": "PEDIDO_ACESSO",
    "Reclamação": "RECLAMACAO",
    "Reclamacao": "RECLAMACAO",
    "RECLAMACAO": "RECLAMACAO",
    "Denúncia": "DENUNCIA",
    "Denuncia": "DENUNCIA",
    "DENUNCIA": "DENUNCIA",
    "Sugestão": "SUGESTAO",
    "Sugestao": "SUGESTAO",
    "SUGESTAO": "SUGESTAO",
    "Elogio": "ELOGIO",
    "ELOGIO": "ELOGIO",
}


def get_or_create_default_unidade() -> UnidadeGestora:
    unidade = UnidadeGestora.query.first()
    if unidade:
        return unidade

    unidade = UnidadeGestora(
        codigo="UG-PADRAO",
        nome="Unidade Gestora Padrao",
        sigla="UGP",
    )
    db.session.add(unidade)
    db.session.commit()
    return unidade


def generate_protocolo() -> str:
    while True:
        suffix = str(uuid.uuid4().int)[:8]
        protocolo = f"ESIC-{datetime.utcnow():%Y%m%d}-{suffix}"
        if not EsicPedido.query.filter_by(protocolo=protocolo).first():
            return protocolo


def is_valid_email(value: str) -> bool:
    if not value or "@" not in value or value.startswith("@") or value.endswith("@"):
        return False
    return "." in value.split("@", 1)[1]


@app.get("/")
def home():
    infos = PortalInformacao.query.filter_by(ativo=True).order_by(
        PortalInformacao.secao, PortalInformacao.ordem, PortalInformacao.titulo
    )
    infos_por_secao = {
        "FINANCEIROS": [i for i in infos if i.secao == "FINANCEIROS"],
        "PRESTACAO": [i for i in infos if i.secao == "PRESTACAO"],
        "CONTRATACOES": [i for i in infos if i.secao == "CONTRATACOES"],
        "POLITICAS": [i for i in infos if i.secao == "POLITICAS"],
    }
    return render_template("portal_transparencia.html", infos_por_secao=infos_por_secao)


@app.post("/api/esic/submit/")
def submit_esic_request():
    tipo_input = (request.form.get("tipo") or "").strip()
    descricao = (request.form.get("descricao") or "").strip()
    email = (request.form.get("email") or "").strip()
    nome = (request.form.get("nome") or "").strip()
    setor = (request.form.get("setor") or "").strip()
    formato_resposta = (request.form.get("formato_resposta") or "").strip()
    anexo = request.files.get("anexo")

    if not descricao:
        return jsonify({"error": "Descricao do pedido e obrigatoria."}), 400

    if email and not is_valid_email(email):
        return jsonify({"error": "Email invalido."}), 400

    saved_file = None
    if anexo and anexo.filename:
        filename = secure_filename(anexo.filename)
        if not filename.lower().endswith(".pdf"):
            return jsonify({"error": "Apenas arquivos PDF sao permitidos."}), 400

        saved_name = f"pedido_{uuid.uuid4().hex[:8]}.pdf"
        destination = UPLOAD_DIR / saved_name
        anexo.save(destination)
        saved_file = f"/media/esic_anexos/{saved_name}"

    tipo = TIPO_ESIC_MAP.get(tipo_input, "PEDIDO_ACESSO")
    protocolo = generate_protocolo()
    prazo = datetime.utcnow() + timedelta(days=20)

    extras = []
    if nome:
        extras.append(f"Nome: {nome}")
    if setor and setor != "Selecione...":
        extras.append(f"Setor: {setor}")
    if formato_resposta:
        extras.append(f"Formato de resposta: {formato_resposta}")

    descricao_expandida = descricao
    if extras:
        descricao_expandida = descricao + "\n\n" + "\n".join(extras)

    unidade = get_or_create_default_unidade()
    pedido = EsicPedido(
        protocolo=protocolo,
        tipo=tipo,
        descricao=descricao_expandida,
        status="ABERTO",
        email=email or None,
        anexo=saved_file,
        prazo=prazo,
        unidade_id=unidade.id,
    )
    db.session.add(pedido)
    db.session.commit()

    return jsonify({"message": "Solicitacao registrada com sucesso.", "protocolo": protocolo}), 201


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
