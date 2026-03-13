import click
from build_engine import build_image
from runtime import run_image
from image_manager import list_images, remove_image
from lan.registry_server import run_server
from lan.push import push_image
from lan.pull import pull_image

@click.group()

def cli():
    """Docksmith CLI"""
    pass

@cli.command()
@click.option('-t', '--tag', required=True, help='name:tag')
@click.option('--no-cache', is_flag=True, default=False, help='Skip cache lookups and writes')
@click.argument('context', type=click.Path(exists=True), default='.')
def build(tag, no_cache, context):
    """Build an image from a Docksmithfile in CONTEXT"""
    name, tagname = tag.split(':') if ':' in tag else (tag, 'latest')
    build_image(context, name, tagname, no_cache=no_cache)

@cli.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option('-e', '--env', multiple=True, help='Environment override KEY=VALUE (repeatable)')
@click.argument('image', required=True)
@click.argument('cmd', nargs=-1)
@click.pass_context
def run(ctx, env, image, cmd):
    """Run an image by name:tag. Optionally override CMD with CMD args and set -e KEY=VAL."""
    name, tag = image.split(':') if ':' in image else (image, 'latest')
    env_overrides = {}
    for e in env:
        if '=' in e:
            k, v = e.split('=', 1)
            env_overrides[k] = v
    cmd_override = list(cmd) if cmd else None
    run_image(name, tag, cmd_override=cmd_override, env_overrides=env_overrides)

@cli.command()
def images():
    """List local images"""
    imgs = list_images()
    # imgs is list of dicts with name, tag, id, created
    click.echo(f"{'NAME':20} {'TAG':10} {'ID':12} {'CREATED'}")
    for it in imgs:
        click.echo(f"{it['name']:20} {it['tag']:10} {it['id']:12} {it['created']}")

@cli.command()
@click.argument('image')
def rmi(image):
    """Remove an image"""
    name, tag = image.split(':') if ':' in image else (image, 'latest')
    remove_image(name, tag)

@cli.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=5000)
def serve(host, port):
    """Run the LAN registry server"""
    run_server(host, port)

@cli.command()
@click.argument('image')
@click.argument('server')
def push(image, server):
    """Push an image to a LAN registry (server is ip:port)"""
    name, tag = image.split(':') if ':' in image else (image, 'latest')
    push_image(name, tag, server)

@cli.command()
@click.argument('image')
@click.argument('server')
def pull(image, server):
    """Pull an image from a LAN registry (server is ip:port)"""
    name, tag = image.split(':') if ':' in image else (image, 'latest')
    pull_image(name, tag, server)

if __name__ == '__main__':
    cli()
