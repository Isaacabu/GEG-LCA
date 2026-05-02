from rest_framework import serializers
from .models import (
    Material, MaterialSchicht, Konstruktion, KonstruktionSchicht,
    FensterTyp, TürTyp, SonnenschutzTyp, Gebäude, Bauteil
)


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'name', 'description', 'rohdichte', 'lambda_value', 'c_specific', 'mu_value']


class MaterialSchichtSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    r_value = serializers.SerializerMethodField()
    
    class Meta:
        model = MaterialSchicht
        fields = ['id', 'material', 'material_name', 'thickness_mm', 'r_value']
    
    def get_r_value(self, obj):
        return round(obj.r_value, 4)


class KonstruktionSchichtSerializer(serializers.ModelSerializer):
    schicht_detail = MaterialSchichtSerializer(source='schicht', read_only=True)
    
    class Meta:
        model = KonstruktionSchicht
        fields = ['id', 'order', 'schicht', 'schicht_detail']


class KonstruktionSerializer(serializers.ModelSerializer):
    schichten = KonstruktionSchichtSerializer(source='konstruktionschicht_set', many=True, read_only=True)
    u_value = serializers.SerializerMethodField()
    r_value_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Konstruktion
        fields = [
            'id', 'name', 'typ', 'get_typ_display', 'description',
            'schichten', 'r_si', 'r_se', 'u_value', 'r_value_total'
        ]
    
    def get_u_value(self, obj):
        return round(obj.u_value, 4)
    
    def get_r_value_total(self, obj):
        return round(obj.r_value_total, 4)


class FensterTypSerializer(serializers.ModelSerializer):
    class Meta:
        model = FensterTyp
        fields = ['id', 'name', 'description', 'u_w', 'g_value', 'psi_edge']


class TürTypSerializer(serializers.ModelSerializer):
    class Meta:
        model = TürTyp
        fields = ['id', 'name', 'u_value', 'luftdichtheit']


class SonnenschutzTypSerializer(serializers.ModelSerializer):
    class Meta:
        model = SonnenschutzTyp
        fields = ['id', 'name', 'position', 'typ', 'reduktionsfaktor']


class BauteilSerializer(serializers.ModelSerializer):
    konstruktion_name = serializers.CharField(source='konstruktion.name', read_only=True)
    fenster_typ_name = serializers.CharField(source='fenster_typ.name', read_only=True)
    sonnenschutz_name = serializers.CharField(source='sonnenschutz.name', read_only=True)
    transmissionsverlust = serializers.SerializerMethodField()
    
    class Meta:
        model = Bauteil
        fields = [
            'id', 'gebäude', 'name', 'orientierung', 'fläche',
            'konstruktion', 'konstruktion_name',
            'fenster_typ', 'fenster_typ_name', 'fenster_fläche',
            'sonnenschutz', 'sonnenschutz_name',
            'transmissionsverlust'
        ]
    
    def get_transmissionsverlust(self, obj):
        return round(obj.transmissionsverlust, 2)


class GebäudeSerializer(serializers.ModelSerializer):
    bauteile = BauteilSerializer(many=True, read_only=True)
    
    class Meta:
        model = Gebäude
        fields = ['id', 'name', 'standort', 'bgf', 'gradstunden', 'bauteile', 'created_at', 'updated_at']
