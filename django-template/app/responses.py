from django.http import JsonResponse


class BaseJsonResponse(JsonResponse):
    def __init__(self, *args, **kwargs):
        super(BaseJsonResponse, self).__init__(
            *args,
            safe=False,
            json_dumps_params={'ensure_ascii': False},
            **kwargs
        )


class SuccessJsonResponse(BaseJsonResponse):
    def __init__(self, data=None, **kwargs):
        super(SuccessJsonResponse, self).__init__(data, **kwargs)


class ErrorJsonResponse(BaseJsonResponse):
    def __init__(self, err_code=400, message=None, **kwargs):
        super(ErrorJsonResponse, self).__init__(
            message,
            **kwargs,
            status=err_code,
        )
