# -*- coding: utf-8 -*-

import click

import os
import subprocess


class Config(object):
    def __init__(self):
        self.port = '8080'
        self.docker_image = 'ccf/php:dev'

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--port', '-p', type=click.INT, default='8080',
        help='Puerto usado por el servidor')
@pass_config
def cli(config, port):
    '''Apache+PHP Development Server'''
    config.port = port


###########
#  Start  #
###########

@click.command()
@click.option(
        '--document-root', '-d',
        type=click.Path(exists=True, file_okay=False),
        default='.',
        help='Directorio donde se encuentran los ficheros que van a ser servidos'
)
@pass_config
def start(config, document_root):
    '''Inicia el servidor'''
    click.echo('Iniciando servidor en puerto %s' % config.port)
    droot_expanded = os.path.abspath(os.path.expanduser(document_root))
    shellcmd = 'docker run  -d  -p {port}:80  -v {document_root}:/var/www/html --name=apds{port} {docker_image}'.format(
        port=config.port,
        document_root=droot_expanded,
        docker_image=config.docker_image
    )
    subprocess.Popen(shellcmd)


##########
#  Stop  #
##########

@click.command()
@pass_config
def stop(config):
    '''Detiene el servidor'''
    click.echo('Deteniendo servidor')
    shellcmd = 'docker rm -f apds{port}'.format(
        port=config.port
    )
    subprocess.Popen(shellcmd)


#############
#  Restart  #
#############

@click.command()
@pass_config
def restart(config):
    '''Reinicia el servidor'''
    click.echo('Reiniciando servidor')
    shellcmd = 'docker restart apds{port}'.format(
        port=config.port
    )
    subprocess.Popen(shellcmd)


#########
#  Run  #
#########

@click.command()
@click.argument('comando', nargs=1)
@pass_config
def run(config, comando):
    '''Ejecuta un comando que esté disponible dentro del contenedor del servidor'''
    click.echo('Ejecutando %s' % comando)
    shellcmd = 'docker exec -it apds{port} {comando}'.format(
        port=config.port,
        comando=comando
    )
    subprocess.Popen(shellcmd)


##########
#  Logs  #
##########

@click.command()
@click.option('--follow', '-f', is_flag=True,
        help=u'Muestra las novedades del log según vayan apareciendo')
@click.option('--clear', '-c', is_flag=True,
        help=u'Elimina los contenidos del archivo de logs')
@pass_config
def logs(config, follow, clear):
    '''Muestra el log de errores de PHP'''
    click.echo('Not implemented yet')



cli.add_command(start)
cli.add_command(stop)
cli.add_command(restart)

cli.add_command(run)
cli.add_command(logs)
