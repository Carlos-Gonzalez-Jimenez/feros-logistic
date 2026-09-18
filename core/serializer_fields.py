from django.conf import settings
from django.utils.translation import get_language_from_request, get_language
from parler.models import TranslatableModelMixin
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializerMixin, TranslatableModelSerializer
from rest_framework import serializers


class FlattenedTranslatableModelSerializer(TranslatableModelSerializerMixin, serializers.ModelSerializer):

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if not isinstance(instance, TranslatableModelMixin):
            return ret

        request = self.context.get('request')
        language_code = get_language_from_request(request) if request else get_language()

        try:
            translation = instance.translations.get(language_code=language_code)
        except instance.translations.model.DoesNotExist:
            translation = None
            default_lang = settings.PARLER_DEFAULT_LANGUAGE_CODE
            if default_lang != language_code:
                translation = instance.translations.filter(language_code=default_lang).first()

        if translation:
            for field in translation._meta.fields:
                field_name = field.name
                if field_name in ('id', 'language_code', 'master'):
                    continue
                if field_name not in ret:
                    ret[field_name] = getattr(translation, field_name)
        return ret


class FullTranslatableModelSerializer(TranslatableModelSerializer):

    def get_fields(self):
        fields = super().get_fields()
        model = self.Meta.model
        to_remove = [name for name in fields.keys() if name.endswith('_t')]
        for name in to_remove:
            fields.pop(name)
        if hasattr(model, '_parler_meta') and not fields.get('translations'):
            fields['translations'] = TranslatedFieldsField(shared_model=self.Meta.model)
        return fields

    # def __to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     if not isinstance(instance, TranslatableModelMixin):
    #         return ret
    #
    #     request = self.context.get('request')
    #     if request:
    #         language_code = get_language_from_request(request)
    #     else:
    #         language_code = translation.get_language()
    #
    #     if not language_code:
    #         return ret
    #
    #     try:
    #         translation = instance.translations.get(language_code=language_code)
    #     except instance.translations.model.DoesNotExist:
    #         default_lang = settings.PARLER_DEFAULT_LANGUAGE_CODE
    #         if default_lang and default_lang != language_code:
    #             try:
    #                 translation = instance.translations.get(language_code=default_lang)
    #             except instance.translations.model.DoesNotExist:
    #                 translation = None
    #         else:
    #             translation = None
    #
    #     if translation:
    #         for field in translation._meta.fields:
    #             field_name = field.name
    #             if field_name in ('id', 'language_code', 'master'):
    #                 continue
    #             if field_name not in ret:
    #                 ret[field_name] = getattr(translation, field_name)
    #     return ret

    def to_representation(self, instance):
        request = self.context.get('request')
        if request:
            language_code = get_language_from_request(request)
        else:
            from django.utils import translation
            language_code = translation.get_language()

        rep = super().to_representation(instance)
        translations = rep.get('translations', {})
        fields = translations.get(language_code, translations.get(settings.PARLER_DEFAULT_LANGUAGE_CODE, {}))

        rep.update(**fields)
        return rep
