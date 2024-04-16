from rest_framework import serializers


class SerializerMethodDecimalField(
    serializers.DecimalField,
    serializers.SerializerMethodField,
):
    def __init__(self, method_name=None, **kwargs):
        serializers.SerializerMethodField.__init__(self, method_name)
        serializers.DecimalField.__init__(self, **kwargs)

    def to_representation(self, value):
        temp = serializers.SerializerMethodField.to_representation(self, value)
        return serializers.DecimalField.to_representation(self, temp)
