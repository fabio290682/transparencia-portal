from rest_framework import serializers
from .models import UnidadeGestora, Despesa, Licitacao, Servidor, EsicPedido

class UnidadeGestoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeGestora
        fields = '__all__'

class DespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Despesa
        fields = '__all__'

class LicitacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licitacao
        fields = '__all__'

class ServidorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servidor
        fields = '__all__'

class EsicPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EsicPedido
        fields = '__all__'
