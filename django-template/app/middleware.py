def logging_middleware(get_response):
    # One-time configuration and initialization.
    def middleware(request):
        print('request.endpoint: ' + request.path)
        response = get_response(request)
        print(f'response.status_code: {response.status_code}' )
        return response
    return middleware
