import requests


def _host(server: str) -> str:
    return server if server.startswith('http') else f'http://{server}'


def list_registry_images(server: str) -> list:
    host = _host(server)
    url = f"{host}/images"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def delete_registry_image(name: str, tag: str, server: str):
    host = _host(server)
    name_tag = f"{name}_{tag}"
    url = f"{host}/images/{name_tag}"
    r = requests.delete(url)
    if r.status_code == 404:
        raise RuntimeError(f'Registry image not found: {name}:{tag}')
    r.raise_for_status()
