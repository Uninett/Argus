Convert Django ValidationErrors to DRF ValidationErrors. This makes it possible
to move some validation from API model serializers to the actual model, which
means validating only once and the API and future Django frontend seeing the
same errors.
