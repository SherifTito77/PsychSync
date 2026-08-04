import asyncio

from app.main import app


def list_routes():
    print(f"{'Method':<10} {'Path':<50} {'Name'}")
    print("-" * 80)
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = ", ".join(route.methods)
            print(f"{methods:<10} {route.path:<50} {route.name}")
        else:
            print(f"{'ANY':<10} {route.path:<50} {route.name}")


if __name__ == "__main__":
    list_routes()
