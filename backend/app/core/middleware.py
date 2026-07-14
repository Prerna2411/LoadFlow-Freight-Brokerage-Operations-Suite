from fastapi.middleware.cors import CORSMiddleware


def cors_options(origins: list[str]) -> dict:
    return {
        "middleware_class": CORSMiddleware,
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
