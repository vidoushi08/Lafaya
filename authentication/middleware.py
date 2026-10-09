import re


class CustomerVerificationOriginMiddleware:
    verification_path = re.compile(
        r"/authentication/verify/[^/]+/[^/]+/"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method == "POST"
            and self.verification_path.fullmatch(request.path_info)
            and request.headers.get("Origin") == "null"
            and request.headers.get("Sec-Fetch-Site") == "same-origin"
        ):
            request.META["HTTP_ORIGIN"] = (
                f"{request.scheme}://{request.get_host()}"
            )

        return self.get_response(request)
