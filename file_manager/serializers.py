# serializers.py
from rest_framework import serializers

from .models import Folder, File


class FolderBreadcrumbSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'name']


class FolderSerializer(serializers.ModelSerializer):
    path = serializers.ReadOnlyField()

    # subfolder_count = serializers.IntegerField(read_only=True)
    # file_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Folder
        fields = serializers.ALL_FIELDS


class FolderCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ["id", "name", "parent"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        parent = attrs.get("parent")
        instance = self.instance
        if instance and parent:
            node = parent
            while node:
                if node.pk == instance.pk:
                    raise serializers.ValidationError(
                        {"parent": "No puedes mover una carpeta dentro de sí misma o de un descendiente."}
                    )
                node = node.parent
        return attrs


class FileSerializer(serializers.ModelSerializer):
    folder_id = serializers.PrimaryKeyRelatedField(read_only=True)
    folder_path = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = File
        exclude = ['folder']

    def get_folder_path(self, obj):
        return obj.folder.path if obj.folder else "/"

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class FileCRUDSerializer(serializers.ModelSerializer):
    folder_id = serializers.PrimaryKeyRelatedField(queryset=Folder.objects.all(), source="folder")

    class Meta:
        model = File
        fields = ["id", "file", "folder_id"]

    def validate(self, attrs):
        file = attrs.get("file")
        name = file.name
        folder = attrs.get("folder")
        if File.objects.filter(folder=folder, name=name).exists():
            raise serializers.ValidationError({"file": "Ya tienes un archivo con ese nombre en esta carpeta."})
        attrs['name'] = name
        attrs['mime_type'] = getattr(file, 'content_type', None)
        return attrs


class FolderContentSerializer(serializers.ModelSerializer):
    breadcrumbs = serializers.SerializerMethodField()
    folder = serializers.SerializerMethodField()
    subfolders = FolderSerializer(many=True)
    files = FileSerializer(many=True)

    def get_folder(self, obj):
        return FolderSerializer(obj).data

    def get_breadcrumbs(self, obj):
        parents = [obj]
        while obj.parent:
            parents.append(obj.parent)
            obj = obj.parent
        parents.reverse()
        return FolderBreadcrumbSerializer(parents, many=True).data

    class Meta:
        model = Folder
        fields = ['folder', 'subfolders', 'files', "breadcrumbs"]
