import html
import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.request import urlopen

from django.core.management.base import BaseCommand, CommandError

from core.models import PortalInformacao, Projeto


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_th = False
        self.in_td = False
        self.current = ""
        self.current_key: str | None = None
        self.rows: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "th":
            self.in_th = True
            self.current = ""
        elif tag == "td":
            self.in_td = True
            self.current = ""
        elif tag == "br" and (self.in_th or self.in_td):
            self.current += "\n"

    def handle_endtag(self, tag: str) -> None:
        if tag == "th":
            self.in_th = False
            self.current_key = self.current.strip()
        elif tag == "td":
            self.in_td = False
            if self.current_key:
                self.rows.append((self.current_key, self.current.strip()))

    def handle_data(self, data: str) -> None:
        if self.in_th or self.in_td:
            self.current += html.unescape(data)


class Command(BaseCommand):
    help = "Sincroniza projetos e ofícios do portal WordPress de transparência."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--base-url",
            default="https://institutomeiodomundo.org/transparencia",
            help="URL base do portal WordPress.",
        )
        parser.add_argument(
            "--categories-file",
            help="Arquivo JSON local com categorias do WP.",
        )
        parser.add_argument(
            "--posts-file",
            help="Arquivo JSON local com posts do WP.",
        )

    def handle(self, *args, **options) -> None:
        categories = self._load_categories(options["base_url"], options.get("categories_file"))
        posts = self._load_posts(options["base_url"], options.get("posts_file"))

        category_ids = {item["slug"]: item["id"] for item in categories}
        termo_id = category_ids.get("termo-de-fomento")
        andamento_id = category_ids.get("em-andamento")
        finalizado_id = category_ids.get("finalizados")
        oficio_id = category_ids.get("oficio-de-entrega-da-prestacao-de-contas")

        if not termo_id or not oficio_id:
            raise CommandError("Categorias essenciais do portal WordPress nao foram encontradas.")

        projetos_criados = 0
        projetos_atualizados = 0
        oficios_criados = 0
        oficios_atualizados = 0

        posts.sort(key=lambda item: item.get("date", ""), reverse=True)

        for ordem, post in enumerate(posts, start=1):
            categorias_post = set(post.get("categories", []))
            parsed = self._parse_post(post)

            if termo_id in categorias_post:
                defaults = self._build_project_defaults(
                    parsed=parsed,
                    ordem=ordem,
                    andamento_id=andamento_id,
                    finalizado_id=finalizado_id,
                    categorias_post=categorias_post,
                )
                _, created = Projeto.objects.update_or_create(
                    titulo=defaults["titulo"],
                    defaults=defaults,
                )
                if created:
                    projetos_criados += 1
                else:
                    projetos_atualizados += 1
                continue

            if oficio_id in categorias_post:
                defaults = self._build_oficio_defaults(parsed=parsed, ordem=ordem)
                _, created = PortalInformacao.objects.update_or_create(
                    secao="PRESTACAO",
                    titulo=defaults["titulo"],
                    defaults=defaults,
                )
                if created:
                    oficios_criados += 1
                else:
                    oficios_atualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Sincronizacao concluida. "
                f"Projetos criados: {projetos_criados}, atualizados: {projetos_atualizados}. "
                f"Oficios criados: {oficios_criados}, atualizados: {oficios_atualizados}.",
            ),
        )

    def _load_categories(self, base_url: str, categories_file: str | None) -> list[dict[str, Any]]:
        if categories_file:
            with open(categories_file, encoding="utf-8-sig") as handle:
                return json.load(handle)
        return self._fetch_json(f"{base_url.rstrip('/')}/wp-json/wp/v2/categories?per_page=100")

    def _load_posts(self, base_url: str, posts_file: str | None) -> list[dict[str, Any]]:
        if posts_file:
            with open(posts_file, encoding="utf-8-sig") as handle:
                return json.load(handle)
        return self._fetch_json(f"{base_url.rstrip('/')}/wp-json/wp/v2/posts?per_page=100&_embed")

    def _fetch_json(self, url: str) -> list[dict[str, Any]]:
        with urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _parse_post(self, post: dict[str, Any]) -> dict[str, Any]:
        content = html.unescape(post.get("content", {}).get("rendered", ""))
        parser = TableParser()
        parser.feed(content)
        table = {key: value for key, value in parser.rows if key}
        title = html.unescape(re.sub(r"<[^>]+>", "", post.get("title", {}).get("rendered", ""))).strip()
        return {
            "title": title,
            "content": content,
            "table": table,
            "document_url": self._extract_document_url(content, post.get("link", "")),
        }

    def _extract_document_url(self, content: str, fallback: str) -> str:
        for match in re.findall(r'https://[^"\'\s>]+', content):
            lowered = match.lower()
            if ".pdf" in lowered or ".xls" in lowered or ".xlsx" in lowered:
                return match
        return fallback

    def _build_project_defaults(
        self,
        *,
        parsed: dict[str, Any],
        ordem: int,
        andamento_id: int | None,
        finalizado_id: int | None,
        categorias_post: set[int],
    ) -> dict[str, Any]:
        table = parsed["table"]
        title = parsed["title"]
        status = "FINALIZADO"
        if andamento_id and andamento_id in categorias_post:
            status = "EM_ANDAMENTO"
        elif finalizado_id and finalizado_id in categorias_post:
            status = "FINALIZADO"
        return {
            "titulo": title,
            "subtitulo": table.get("Número do Instrumento", ""),
            "status": status,
            "icone": self._icon_for_title(title),
            "valor": table.get("Recurso Financeiro", ""),
            "instrumento": table.get("Número do Instrumento", ""),
            "recurso_financeiro": table.get("Recurso Financeiro", ""),
            "fonte_recurso_estadual": table.get("Fonte de Recurso Estadual (500)", ""),
            "fonte_recurso_federal": table.get("Fonte de Recurso Federal (706)", ""),
            "autoria_emenda": table.get("Autoria da Emenda", ""),
            "nome_projeto": table.get("Nome do Projeto", ""),
            "valor_repassado": "",
            "valor_global": table.get("Valor Global", ""),
            "objeto": table.get("Objeto", ""),
            "data_inicio": table.get("Data de Início", ""),
            "data_finalizacao": table.get("Data de Finalização", ""),
            "justificativa": table.get("Justificativa", ""),
            "dados_orcamentarios": table.get("Dados Orçamentários", "").replace("\n", " · "),
            "documento_link": parsed["document_url"],
            "documento_label": "⬇ Baixar Documento PDF",
            "ordem": ordem,
            "ativo": True,
        }

    def _build_oficio_defaults(self, *, parsed: dict[str, Any], ordem: int) -> dict[str, Any]:
        table = parsed["table"]
        projeto = table.get("Nome do Projeto") or parsed["title"]
        instrumento = table.get("Número do Instrumento", "")
        descricao = f"Ofício de entrega da prestação de contas do projeto {projeto}."
        if instrumento:
            descricao += f" Instrumento: {instrumento}."
        return {
            "secao": "PRESTACAO",
            "titulo": parsed["title"],
            "descricao": descricao,
            "link": parsed["document_url"],
            "ordem": ordem,
            "ativo": True,
        }

    def _icon_for_title(self, title: str) -> str:
        title_upper = title.upper()
        if "CORRIDA" in title_upper:
            return "🏃"
        if "DESFILE" in title_upper:
            return "🎖️"
        if "FÉRIAS" in title_upper:
            return "🌴"
        if "SHOW MUSICAL" in title_upper:
            return "🎶"
        if "ESPET" in title_upper or "CORPO DE CRISTO" in title_upper:
            return "🎭"
        if "CALÇOENE" in title_upper:
            return "🏖️"
        if "CONEXÃO AMAZÔNIA" in title_upper:
            return "🌿"
        if "NATAL" in title_upper:
            return "🎄"
        return "📌"
