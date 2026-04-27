import json
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook
from rest_framework import status
from rest_framework.test import APITestCase

from .models import EsicPedido, PortalInformacao, Projeto


class EsicSubmitApiTests(APITestCase):
    def test_submit_esic_request_success(self):
        payload = {
            "tipo": "Acesso à Informação",
            "descricao": "Preciso do relatório anual.",
            "email": "cidadao@example.com",
            "nome": "Maria Silva",
            "setor": "Financeiro",
            "formato_resposta": "E-mail",
        }

        response = self.client.post("/api/esic/submit/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("protocolo", response.data)
        self.assertEqual(EsicPedido.objects.count(), 1)

        pedido = EsicPedido.objects.first()
        self.assertEqual(pedido.tipo, "PEDIDO_ACESSO")
        self.assertEqual(pedido.status, "ABERTO")
        self.assertEqual(pedido.email, "cidadao@example.com")
        self.assertIsNotNone(pedido.unidade)

    def test_submit_esic_request_without_description_returns_400(self):
        response = self.client.post(
            "/api/esic/submit/",
            {"tipo": "Reclamação", "descricao": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EsicPedido.objects.count(), 0)

    def test_submit_esic_request_invalid_email_returns_400(self):
        response = self.client.post(
            "/api/esic/submit/",
            {"tipo": "Sugestão", "descricao": "Teste", "email": "email-invalido"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EsicPedido.objects.count(), 0)

    def test_submit_esic_request_with_pdf_attachment_success(self):
        pdf = SimpleUploadedFile(
            "pedido.pdf",
            b"%PDF-1.4 test",
            content_type="application/pdf",
        )
        payload = {
            "tipo": "Elogio",
            "descricao": "Pedido com anexo",
            "email": "anexo@example.com",
            "anexo": pdf,
        }

        response = self.client.post("/api/esic/submit/", payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pedido = EsicPedido.objects.first()
        self.assertIsNotNone(pedido)
        self.assertTrue(bool(pedido.anexo))

    def test_submit_esic_request_with_non_pdf_attachment_returns_400(self):
        txt = SimpleUploadedFile(
            "pedido.txt",
            b"texto simples",
            content_type="text/plain",
        )
        payload = {
            "tipo": "Elogio",
            "descricao": "Pedido com arquivo invalido",
            "anexo": txt,
        }

        response = self.client.post("/api/esic/submit/", payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HealthAndRegisterApiTests(APITestCase):
    def test_health_endpoint_returns_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("status"), "ok")

    @override_settings(ALLOW_PUBLIC_REGISTRATION=False)
    def test_register_user_disabled_returns_403(self):
        payload = {
            "username": "qa_user",
            "password": "SenhaTeste123!",
            "email": "qa@example.com",
        }
        response = self.client.post("/api/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PublicPortalInfoApiTests(APITestCase):
    def test_public_portal_info_returns_grouped_items(self):
        PortalInformacao.objects.create(
            secao="POLITICAS",
            titulo="Lei Geral de Proteção de Dados (LGPD)",
            descricao="Lei no 13.709/2018.",
            link="https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/L13709.htm",
            ordem=1,
            ativo=True,
        )
        PortalInformacao.objects.create(
            secao="FINANCEIROS",
            titulo="Relatório Financeiro 2025",
            descricao="Balanço anual.",
            ordem=1,
            ativo=True,
        )

        response = self.client.get("/api/public/portal-info/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("items", response.data)
        self.assertIn("POLITICAS", response.data["items"])
        self.assertIn("FINANCEIROS", response.data["items"])
        self.assertEqual(len(response.data["items"]["POLITICAS"]), 1)
        self.assertEqual(len(response.data["items"]["FINANCEIROS"]), 1)

    def test_public_portal_info_does_not_return_inactive_items(self):
        PortalInformacao.objects.create(
            secao="POLITICAS",
            titulo="Documento inativo",
            descricao="Não deve aparecer.",
            ordem=5,
            ativo=False,
        )

        response = self.client.get("/api/public/portal-info/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]["POLITICAS"]), 0)


class SeedPortalInfoCommandTests(TestCase):
    def test_seed_portal_info_creates_default_items_idempotently(self):
        call_command("seed_portal_info")
        self.assertEqual(PortalInformacao.objects.filter(secao="POLITICAS").count(), 2)

        call_command("seed_portal_info")
        self.assertEqual(PortalInformacao.objects.filter(secao="POLITICAS").count(), 2)

        self.assertTrue(
            PortalInformacao.objects.filter(
                titulo="Lei Geral de Proteção de Dados (LGPD)",
                ativo=True,
            ).exists(),
        )
        self.assertTrue(
            PortalInformacao.objects.filter(
                titulo="Lei de Acesso à Informação (LAI)",
                ativo=True,
            ).exists(),
        )


    def test_sync_wordpress_portal_imports_projects_and_oficios_from_local_files(self):
        categories_path = Path("test-wordpress-categories.json")
        posts_path = Path("test-wordpress-posts.json")

        categories_path.write_text(
            json.dumps(
                [
                    {"id": 13, "slug": "termo-de-fomento"},
                    {"id": 27, "slug": "em-andamento"},
                    {"id": 28, "slug": "finalizados"},
                    {"id": 37, "slug": "oficio-de-entrega-da-prestacao-de-contas"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        posts_path.write_text(
            json.dumps(
                [
                    {
                        "date": "2026-02-05T00:00:00",
                        "categories": [27, 13],
                        "title": {"rendered": "Projeto Teste"},
                        "content": {
                            "rendered": (
                                '<figure class="wp-block-table"><table><tbody>'
                                "<tr><th>Número do Instrumento</th><td>001/2026</td></tr>"
                                "<tr><th>Recurso Financeiro</th><td>R$ 10.000,00</td></tr>"
                                "<tr><th>Nome do Projeto</th><td>Projeto Teste</td></tr>"
                                "<tr><th>Data de Início</th><td>01/01/2026</td></tr>"
                                "<tr><th>Data de Finalização</th><td>31/01/2026</td></tr>"
                                "</tbody></table></figure>"
                                '<div class="wp-block-file"><a href="https://exemplo.com/projeto.pdf">PDF</a></div>'
                            ),
                        },
                        "link": "https://exemplo.com/projeto-teste/",
                    },
                    {
                        "date": "2026-02-06T00:00:00",
                        "categories": [37],
                        "title": {"rendered": "Ofício Projeto Teste"},
                        "content": {
                            "rendered": (
                                '<figure class="wp-block-table"><table><tbody>'
                                "<tr><th>Número do Instrumento</th><td>001/2026</td></tr>"
                                "<tr><th>Nome do Projeto</th><td>Projeto Teste</td></tr>"
                                "</tbody></table></figure>"
                                '<div class="wp-block-file"><a href="https://exemplo.com/oficio.pdf">PDF</a></div>'
                            ),
                        },
                        "link": "https://exemplo.com/oficio-projeto-teste/",
                    },
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        try:
            call_command(
                "sync_wordpress_portal",
                categories_file=str(categories_path),
                posts_file=str(posts_path),
            )
        finally:
            categories_path.unlink(missing_ok=True)
            posts_path.unlink(missing_ok=True)

        projeto = Projeto.objects.get(titulo="Projeto Teste")
        self.assertEqual(projeto.instrumento, "001/2026")
        self.assertEqual(projeto.status, "EM_ANDAMENTO")
        self.assertEqual(projeto.documento_link, "https://exemplo.com/projeto.pdf")

        oficio = PortalInformacao.objects.get(secao="PRESTACAO", titulo="Ofício Projeto Teste")
        self.assertIn("Projeto Teste", oficio.descricao)
        self.assertEqual(oficio.link, "https://exemplo.com/oficio.pdf")


class PortalInformacaoArquivoTests(APITestCase):
    def test_accepts_pdf_or_excel_file_for_portal_section(self):
        xlsx = SimpleUploadedFile(
            "financeiro.xlsx",
            b"PK\x03\x04",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        info = PortalInformacao(
            secao="FINANCEIROS",
            titulo="Balançete Mensal",
            descricao="Arquivo importado pelo admin.",
            arquivo=xlsx,
        )
        info.full_clean()

    def test_rejects_invalid_file_extension_for_portal_section(self):
        exe = SimpleUploadedFile("script.exe", b"MZ")
        info = PortalInformacao(
            secao="POLITICAS",
            titulo="Arquivo inválido",
            descricao="Tentativa com extensão proibida.",
            arquivo=exe,
        )

        with self.assertRaises(ValidationError):
            info.full_clean()


class ProjetoArquivoTests(APITestCase):
    def test_accepts_pdf_or_excel_file_for_projeto(self):
        pdf = SimpleUploadedFile(
            "projeto.pdf",
            b"%PDF-1.4 test",
            content_type="application/pdf",
        )
        projeto = Projeto(
            titulo="Projeto Arquivo",
            subtitulo="001/2026",
            status="EM_ANDAMENTO",
            valor="R$ 1,00",
            instrumento="001/2026",
            arquivo=pdf,
        )
        projeto.full_clean()

    def test_rejects_invalid_file_extension_for_projeto(self):
        exe = SimpleUploadedFile("projeto.exe", b"MZ")
        projeto = Projeto(
            titulo="Projeto Arquivo Invalido",
            subtitulo="001/2026",
            status="EM_ANDAMENTO",
            valor="R$ 1,00",
            instrumento="001/2026",
            arquivo=exe,
        )

        with self.assertRaises(ValidationError):
            projeto.full_clean()


class PortalInformacaoImportAdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.user = get_user_model().objects.create_superuser(
            username="admin_import",
            password="SenhaSegura123!",
            email="admin_import@example.com",
        )
        self.client.force_login(self.user)

    def _build_xlsx(self, rows):
        wb = Workbook()
        ws = wb.active
        ws.append(["secao", "titulo", "descricao", "link", "ordem", "ativo"])
        for row in rows:
            ws.append(row)

        buff = BytesIO()
        wb.save(buff)
        buff.seek(0)
        return buff.getvalue()

    def test_importar_planilha_cria_itens_por_aba(self):
        xlsx_content = self._build_xlsx(
            [
                ["FINANCEIROS", "Relatório 2025", "Descrição 1", "https://exemplo.com/a", 1, "sim"],
                ["PRESTACAO", "Prestação 2025", "Descrição 2", "", 2, "não"],
            ],
        )
        upload = SimpleUploadedFile(
            "importacao.xlsx",
            xlsx_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        response = self.client.post(
            reverse("admin:core_portalinformacao_importar_planilha"),
            {"arquivo": upload},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PortalInformacao.objects.count(), 2)
        self.assertTrue(
            PortalInformacao.objects.filter(secao="FINANCEIROS", titulo="Relatório 2025").exists(),
        )
        self.assertTrue(
            PortalInformacao.objects.filter(secao="PRESTACAO", titulo="Prestação 2025").exists(),
        )

    def test_importar_planilha_com_secao_invalida_nao_cria_registro(self):
        xlsx_content = self._build_xlsx(
            [["SECAO_INVALIDA", "Título X", "Descrição X", "", 0, "sim"]],
        )
        upload = SimpleUploadedFile(
            "importacao-invalida.xlsx",
            xlsx_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        response = self.client.post(
            reverse("admin:core_portalinformacao_importar_planilha"),
            {"arquivo": upload},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seção inválida")
        self.assertEqual(PortalInformacao.objects.count(), 0)
