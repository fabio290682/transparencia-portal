from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook
from rest_framework import status
from rest_framework.test import APITestCase

from .models import EsicPedido, PortalInformacao


class EsicSubmitApiTests(APITestCase):
    def test_submit_esic_request_success(self):
        payload = {
            'tipo': 'Acesso à Informação',
            'descricao': 'Preciso do relatório anual.',
            'email': 'cidadao@example.com',
            'nome': 'Maria Silva',
            'setor': 'Financeiro',
            'formato_resposta': 'E-mail',
        }

        response = self.client.post('/api/esic/submit/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('protocolo', response.data)
        self.assertEqual(EsicPedido.objects.count(), 1)

        pedido = EsicPedido.objects.first()
        self.assertEqual(pedido.tipo, 'PEDIDO_ACESSO')
        self.assertEqual(pedido.status, 'ABERTO')
        self.assertEqual(pedido.email, 'cidadao@example.com')
        self.assertIsNotNone(pedido.unidade)

    def test_submit_esic_request_without_description_returns_400(self):
        response = self.client.post(
            '/api/esic/submit/',
            {'tipo': 'Reclamação', 'descricao': ''},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EsicPedido.objects.count(), 0)

    def test_submit_esic_request_invalid_email_returns_400(self):
        response = self.client.post(
            '/api/esic/submit/',
            {'tipo': 'Sugestão', 'descricao': 'Teste', 'email': 'email-invalido'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EsicPedido.objects.count(), 0)

    def test_submit_esic_request_with_pdf_attachment_success(self):
        pdf = SimpleUploadedFile(
            'pedido.pdf',
            b'%PDF-1.4 test',
            content_type='application/pdf',
        )
        payload = {
            'tipo': 'Elogio',
            'descricao': 'Pedido com anexo',
            'email': 'anexo@example.com',
            'anexo': pdf,
        }

        response = self.client.post('/api/esic/submit/', payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pedido = EsicPedido.objects.first()
        self.assertIsNotNone(pedido)
        self.assertTrue(bool(pedido.anexo))

    def test_submit_esic_request_with_non_pdf_attachment_returns_400(self):
        txt = SimpleUploadedFile(
            'pedido.txt',
            b'texto simples',
            content_type='text/plain',
        )
        payload = {
            'tipo': 'Elogio',
            'descricao': 'Pedido com arquivo invalido',
            'anexo': txt,
        }

        response = self.client.post('/api/esic/submit/', payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PortalInformacaoArquivoTests(APITestCase):
    def test_accepts_pdf_or_excel_file_for_portal_section(self):
        xlsx = SimpleUploadedFile(
            'financeiro.xlsx',
            b'PK\x03\x04',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        info = PortalInformacao(
            secao='FINANCEIROS',
            titulo='Balancete Mensal',
            descricao='Arquivo importado pelo admin.',
            arquivo=xlsx,
        )
        info.full_clean()

    def test_rejects_invalid_file_extension_for_portal_section(self):
        exe = SimpleUploadedFile('script.exe', b'MZ')
        info = PortalInformacao(
            secao='POLITICAS',
            titulo='Arquivo invalido',
            descricao='Tentativa com extensao proibida.',
            arquivo=exe,
        )

        with self.assertRaises(ValidationError):
            info.full_clean()


class PortalInformacaoImportAdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.user = get_user_model().objects.create_superuser(
            username='admin_import',
            password='SenhaSegura123!',
            email='admin_import@example.com',
        )
        self.client.force_login(self.user)

    def _build_xlsx(self, rows):
        wb = Workbook()
        ws = wb.active
        ws.append(['secao', 'titulo', 'descricao', 'link', 'ordem', 'ativo'])
        for row in rows:
            ws.append(row)

        buff = BytesIO()
        wb.save(buff)
        buff.seek(0)
        return buff.getvalue()

    def test_importar_planilha_cria_itens_por_aba(self):
        xlsx_content = self._build_xlsx(
            [
                ['FINANCEIROS', 'Relatorio 2025', 'Descricao 1', 'https://exemplo.com/a', 1, 'sim'],
                ['PRESTACAO', 'Prestacao 2025', 'Descricao 2', '', 2, 'nao'],
            ]
        )
        upload = SimpleUploadedFile(
            'importacao.xlsx',
            xlsx_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(
            reverse('admin:core_portalinformacao_importar_planilha'),
            {'arquivo': upload},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PortalInformacao.objects.count(), 2)
        self.assertTrue(
            PortalInformacao.objects.filter(secao='FINANCEIROS', titulo='Relatorio 2025').exists()
        )
        self.assertTrue(
            PortalInformacao.objects.filter(secao='PRESTACAO', titulo='Prestacao 2025').exists()
        )

    def test_importar_planilha_com_secao_invalida_nao_cria_registro(self):
        xlsx_content = self._build_xlsx(
            [['SECAO_INVALIDA', 'Titulo X', 'Descricao X', '', 0, 'sim']]
        )
        upload = SimpleUploadedFile(
            'importacao-invalida.xlsx',
            xlsx_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(
            reverse('admin:core_portalinformacao_importar_planilha'),
            {'arquivo': upload},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Secao invalida')
        self.assertEqual(PortalInformacao.objects.count(), 0)
