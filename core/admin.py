from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path

from .models import (
    UnidadeGestora,
    Despesa,
    Licitacao,
    Servidor,
    EsicPedido,
    PortalInformacao,
)

admin.site.site_header = 'Instituto Meio do Mundo'
admin.site.site_title = 'Admin IMM'
admin.site.index_title = 'Painel Administrativo'


SECAO_MAP = {
    'FINANCEIROS': 'FINANCEIROS',
    'FINANCEIRO': 'FINANCEIROS',
    'PRESTACAO': 'PRESTACAO',
    'PRESTAÇÃO': 'PRESTACAO',
    'CONTRATACOES': 'CONTRATACOES',
    'CONTRATAÇÕES': 'CONTRATACOES',
    'POLITICAS': 'POLITICAS',
    'POLÍTICAS': 'POLITICAS',
}


class PortalInformacaoImportForm(forms.Form):
    arquivo = forms.FileField(
        label='Planilha Excel (.xlsx)',
        help_text='Colunas: secao, titulo, descricao, link, ordem, ativo',
    )


@admin.register(UnidadeGestora)
class UnidadeGestoraAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'sigla')
    search_fields = ('codigo', 'nome', 'sigla')
    readonly_fields = ('id',)


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'categoria', 'exercicio', 'unidade')
    list_filter = ('categoria', 'exercicio', 'unidade')
    search_fields = ('codigo', 'descricao')
    readonly_fields = ('id',)


@admin.register(Licitacao)
class LicitacaoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'modalidade', 'status', 'data_abertura', 'unidade')
    list_filter = ('modalidade', 'status', 'unidade')
    search_fields = ('numero', 'objeto')
    readonly_fields = ('id',)


@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'nome', 'cargo', 'vinculo', 'competencia', 'unidade')
    list_filter = ('vinculo', 'competencia', 'unidade')
    search_fields = ('matricula', 'nome', 'cargo')
    readonly_fields = ('id',)


@admin.register(EsicPedido)
class EsicPedidoAdmin(admin.ModelAdmin):
    list_display = ('protocolo', 'tipo', 'status', 'email', 'prazo', 'unidade')
    list_filter = ('tipo', 'status', 'unidade')
    search_fields = ('protocolo', 'descricao', 'email')
    readonly_fields = ('id',)


@admin.register(PortalInformacao)
class PortalInformacaoAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/portalinformacao/change_list.html'
    list_display = ('secao', 'titulo', 'tipo_documento', 'ordem', 'ativo', 'atualizado_em')
    list_filter = ('secao', 'ativo')
    search_fields = ('titulo', 'descricao', 'link', 'arquivo')
    list_editable = ('ordem', 'ativo')
    readonly_fields = ('id', 'tipo_documento', 'criado_em', 'atualizado_em')
    ordering = ('secao', 'ordem', 'titulo')

    fieldsets = (
        ('Classificação', {'fields': ('secao', 'titulo', 'descricao', 'ordem', 'ativo')}),
        (
            'Documento para o Portal',
            {
                'fields': ('arquivo', 'link', 'tipo_documento'),
                'description': 'Envie PDF/XLS/XLSX para a aba selecionada. O arquivo tem prioridade sobre o link.',
            },
        ),
        ('Controle', {'fields': ('id', 'criado_em', 'atualizado_em')}),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'importar-planilha/',
                self.admin_site.admin_view(self.importar_planilha_view),
                name='core_portalinformacao_importar_planilha',
            ),
        ]
        return custom_urls + urls

    def _to_bool(self, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        texto = str(value).strip().lower()
        return texto in {'1', 'true', 'sim', 's', 'yes', 'y', 'ativo'}

    def _normalizar_secao(self, secao):
        if secao is None:
            return None
        chave = str(secao).strip().upper()
        return SECAO_MAP.get(chave)

    @transaction.atomic
    def _importar_planilha(self, arquivo):
        try:
            from openpyxl import load_workbook
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                'Dependencia ausente: instale openpyxl para usar a importacao de planilhas.'
            ) from exc

        wb = load_workbook(filename=arquivo, data_only=True)
        ws = wb.active

        header = [str(c).strip().lower() if c is not None else '' for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
        header_map = {name: idx for idx, name in enumerate(header)}

        required = {'secao', 'titulo', 'descricao'}
        missing = sorted(required - set(header_map.keys()))
        if missing:
            raise ValueError(f'Colunas obrigatorias ausentes: {", ".join(missing)}')

        created = 0
        for row_index, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(cell is not None and str(cell).strip() for cell in row):
                continue

            secao_raw = row[header_map['secao']] if header_map.get('secao') is not None else None
            secao = self._normalizar_secao(secao_raw)
            if not secao:
                raise ValueError(f'Secao invalida na linha {row_index}: {secao_raw}')

            titulo = str(row[header_map['titulo']]).strip() if row[header_map['titulo']] is not None else ''
            descricao = str(row[header_map['descricao']]).strip() if row[header_map['descricao']] is not None else ''
            if not titulo or not descricao:
                raise ValueError(f'Titulo e descricao sao obrigatorios na linha {row_index}')

            link = ''
            if 'link' in header_map:
                raw_link = row[header_map['link']]
                link = str(raw_link).strip() if raw_link is not None else ''

            ordem = 0
            if 'ordem' in header_map:
                raw_ordem = row[header_map['ordem']]
                if raw_ordem not in (None, ''):
                    try:
                        ordem = int(raw_ordem)
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f'Ordem invalida na linha {row_index}: {raw_ordem}') from exc

            ativo = True
            if 'ativo' in header_map:
                ativo = self._to_bool(row[header_map['ativo']])

            PortalInformacao.objects.create(
                secao=secao,
                titulo=titulo,
                descricao=descricao,
                link=link or None,
                ordem=ordem,
                ativo=ativo,
            )
            created += 1

        return created

    def importar_planilha_view(self, request):
        if request.method == 'POST':
            form = PortalInformacaoImportForm(request.POST, request.FILES)
            if form.is_valid():
                arquivo = form.cleaned_data['arquivo']
                nome = arquivo.name.lower()
                if not nome.endswith('.xlsx'):
                    form.add_error('arquivo', 'Formato invalido. Envie um arquivo .xlsx')
                else:
                    try:
                        created = self._importar_planilha(arquivo)
                    except Exception as exc:
                        form.add_error(None, f'Falha ao importar: {exc}')
                    else:
                        self.message_user(
                            request,
                            f'Importacao concluida com sucesso. Registros criados: {created}',
                            level=messages.SUCCESS,
                        )
                        return redirect('admin:core_portalinformacao_changelist')
        else:
            form = PortalInformacaoImportForm()

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Importar Planilha (Portal Informacoes)',
            'form': form,
        }
        return render(request, 'admin/core/portalinformacao/importar_planilha.html', context)

    @admin.display(description='Tipo de Documento')
    def tipo_documento(self, obj):
        if not obj.arquivo:
            return 'Link Externo' if obj.link else 'Sem documento'
        nome = obj.arquivo.name.lower()
        if nome.endswith('.pdf'):
            return 'PDF'
        if nome.endswith('.xls') or nome.endswith('.xlsx'):
            return 'Excel'
        return 'Arquivo'
