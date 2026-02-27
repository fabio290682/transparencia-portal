from django.core.management.base import BaseCommand

from core.models import PortalInformacao


class Command(BaseCommand):
    help = 'Cria registros iniciais do portal (LGPD e LAI) de forma idempotente.'

    def handle(self, *args, **options):
        defaults = [
            {
                'secao': 'POLITICAS',
                'titulo': 'Lei Geral de Protecao de Dados (LGPD)',
                'descricao': 'Lei no 13.709/2018 (LGPD) - protecao de dados pessoais.',
                'link': 'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/L13709.htm',
                'ordem': 1,
                'ativo': True,
            },
            {
                'secao': 'POLITICAS',
                'titulo': 'Lei de Acesso a Informacao (LAI)',
                'descricao': 'Lei no 12.527/2011 - acesso a informacao publica.',
                'link': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm',
                'ordem': 2,
                'ativo': True,
            },
        ]

        created = 0
        updated = 0
        for item in defaults:
            obj, was_created = PortalInformacao.objects.update_or_create(
                secao=item['secao'],
                titulo=item['titulo'],
                defaults=item,
            )
            if was_created:
                created += 1
            else:
                updated += 1
            self.stdout.write(f'OK: {obj.titulo}')

        self.stdout.write(
            self.style.SUCCESS(f'Seed concluido. Criados: {created}. Atualizados: {updated}.')
        )

