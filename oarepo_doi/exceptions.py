from marshmallow.exceptions import ValidationError

class DoiValidationError(ValidationError):

    def validation_error_to_list_errors(exception):

        errors = exception.data
        return errors