from django.http import Http404


def non_found(request):
    raise Http404
