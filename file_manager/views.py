# views.py
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import Folder, File
from .serializers import (
    FolderSerializer, FolderCRUDSerializer,
    FileSerializer, FileCRUDSerializer, FolderContentSerializer,
)


class FolderViewSet(viewsets.ModelViewSet):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        return Folder.objects.annotate(
            subfolder_count=Count("subfolders", distinct=True),
            file_count=Count("files", distinct=True),
        ).select_related("parent")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return FolderCRUDSerializer
        return FolderSerializer

    @action(detail=False, methods=["get"])
    def root(self, request):
        root_folder = self.get_queryset().filter(root=True).first()
        return Response(FolderContentSerializer(root_folder, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["get"])
    def content(self, request, pk=None):
        folder = self.get_object()
        return Response(FolderContentSerializer(folder, context=self.get_serializer_context()).data)

    @action(detail=False, methods=["get"])
    def tree(self, request):
        """
        Devuelve el árbol completo de carpetas del usuario en formato anidado.
        Útil para pintar un sidebar tipo Drive.
        """
        carpetas = list(self.get_queryset())
        por_padre = {}
        for c in carpetas:
            por_padre.setdefault(c.parent_id, []).append(c)

        def construir(parent_id):
            return [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "path": c.path,
                    "subfolder_count": c.subfolder_count,
                    "file_count": c.file_count,
                    "children": construir(c.id),
                }
                for c in por_padre.get(parent_id, [])
            ]

        return Response(construir(None))


class FileViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        qs = File.objects.filter(owner=self.request.user).select_related("folder")

        # Filtro opcional: /api/files/?folder=<uuid>  o  ?folder=root
        folder_param = self.request.query_params.get("folder")
        if folder_param == "root":
            qs = qs.filter(folder__isnull=True)
        elif folder_param:
            qs = qs.filter(folder_id=folder_param)

        # Búsqueda por nombre: /api/files/?search=manifiesto
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return FileCRUDSerializer
        return FileSerializer

    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        archivos = request.FILES.getlist("archivos")
        if not archivos:
            return Response(
                {"error": "No se enviaron archivos (campo 'archivos')."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        folder_id = request.data.get("folder") or None
        carpeta = None
        if folder_id:
            carpeta = Folder.objects.filter(id=folder_id, owner=request.user).first()
            if not carpeta:
                return Response(
                    {"error": "La carpeta destino no existe o no te pertenece."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        creados, omitidos = [], []
        for archivo in archivos:
            data = {"file": archivo, "folder": carpeta.id if carpeta else None}
            serializer = FileCRUDSerializer(data=data, context=self.get_serializer_context())
            if serializer.is_valid():
                serializer.save(owner=request.user)
                creados.append(serializer.data)
            else:
                omitidos.append({"name": archivo.name, "errors": serializer.errors})

        return Response(
            {"created": creados, "skipped": omitidos},
            status=status.HTTP_201_CREATED if creados else status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        """Mueve un archivo a otra carpeta. Body: {"folder": "<uuid>"} o {"folder": null}."""
        archivo = self.get_object()
        folder_id = request.data.get("folder")

        if folder_id is None:
            archivo.folder = None
        else:
            carpeta = Folder.objects.filter(id=folder_id, owner=request.user).first()
            if not carpeta:
                return Response(
                    {"error": "Carpeta destino inválida."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            archivo.folder = carpeta

        try:
            archivo.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(FileSerializer(archivo, context={"request": request}).data)
