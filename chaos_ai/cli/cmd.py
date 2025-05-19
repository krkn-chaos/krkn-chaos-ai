import click


@click.group()
def main():
    pass


@main.command()
@click.option('--config', '-c', help='Path to chaos ai config file.')
@click.option('--kubeconfig', '-k', help='Path to valid kubeconfig file.')
def run(config, kubeconfig):
    print("DO SOMETHING 2")
