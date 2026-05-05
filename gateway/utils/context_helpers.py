from fastapi import Request

from shared.core import CORRELATION_ID_HEADER, USER_ID_HEADER


def extract_user_id(request: Request, *, debug: bool) -> str:
    """
    Receives a request object and extracts the user id from it.
    If JWT middleware isnt implemented yet, it will return "anonymous" as user id, allowing shared chat for non-logged in users.
    Has a feature, where users will have shared chat if they are not logged in. user_id = "anonymous"

    In debug mode, accepts user_id from query params for testing purposes, allowing developers to simulate different users without needing authentication.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return user_id

    if debug:  # Temporary workaround for testing in debug mode, allowing user_id to be passed as a query parameter
        query_user_id = request.query_params.get("user_id")
        if query_user_id:
            return query_user_id

    # 3. Fallback
    return "anonymous"


def build_context_headers(request: Request) -> dict[str, str]:
    try:
        return {
            CORRELATION_ID_HEADER: request.state.correlation_id,
            USER_ID_HEADER: request.state.user_id,
        }
    except AttributeError:
        # Todo implement custom generic exception handler for this case, and log the error with more context
        raise RuntimeError(
            "Empty or invalid CORRELATION_ID_HEADER or USER_ID_HEADER in request state."
        )
