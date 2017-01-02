# -*- coding: utf-8 -*-

import click

import os
import subprocess
import shlex
import time



def ejecutar_comando(shellcmd):
    p = subprocess.Popen(
        shlex.split(shellcmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    segundos_transcurridos = 0
    click.echo(' ', nl=False)
    while(True):
        poll = p.poll()
        if poll == None:
            click.echo('.', nl=False)
            if segundos_transcurridos > 20:
                p.kill()
                click.echo(click.style(' Falló', fg='red'))

                return -1
        else:
            if poll != 0:
                click.echo(click.style(' Falló', fg='red'))

                return -1
            click.echo(click.style(' Ok', fg='green'))

            return 0

        time.sleep(1)

        segundos_transcurridos += 1


def get_running_containers(docker_path):
    shellcmd = '{docker_path} ps --no-trunc --format "{{{{.Names}}}}\t{{{{.Ports}}}}\t{{{{.Mounts}}}}"'.format(
        docker_path=docker_path
    )
    p = subprocess.Popen(shlex.split(shellcmd), stdout=subprocess.PIPE)

    return p.communicate()[0].split('\n')


class Config(object):
    def __init__(self):
        self.port = '8080'
        self.docker_path = '/usr/bin/docker'
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
    click.echo('Iniciando servidor en puerto %s' % config.port, nl=False)
    droot_expanded = os.path.abspath(os.path.expanduser(document_root))
    shellcmd = '{docker_path} run -d -p {port}:80 -v {document_root}:/var/www/html --name=apds{port} {docker_image}'.format(
        docker_path=config.docker_path,
        port=config.port,
        document_root=droot_expanded,
        docker_image=config.docker_image
    )
    ejecutar_comando(shellcmd)


##########
#  Stop  #
##########

@click.command()
@pass_config
def stop(config):
    '''Detiene el servidor'''
    click.echo('Deteniendo servidor', nl=False)
    shellcmd = '{docker_path} rm -f apds{port}'.format(
        docker_path=config.docker_path,
        port=config.port
    )
    ejecutar_comando(shellcmd)


#############
#  Restart  #
#############

@click.command()
@pass_config
def restart(config):
    '''Reinicia el servidor'''
    click.echo('Reiniciando servidor', nl=False)
    shellcmd = '{docker_path} restart apds{port}'.format(
        docker_path=config.docker_path,
        port=config.port
    )
    ejecutar_comando(shellcmd)


#########
#  Run  #
#########

@click.command()
@click.argument('comando', nargs=1)
@pass_config
def run(config, comando):
    '''Ejecuta un comando que esté disponible dentro del contenedor del servidor'''
    click.echo('Ejecutando: %s' % comando)
    shellcmd = '{docker_path} exec -it apds{port} {comando}'.format(
        docker_path=config.docker_path,
        port=config.port,
        comando=comando
    )
    subprocess.call(shlex.split(shellcmd))


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
    log_path = '/var/log/php_errors.log'
    if clear:
        comando = 'echo "" > {}'.format(log_path)
        shellcmd = '{docker_path} exec -it apds{port} {comando}'.format(
            docker_path=config.docker_path,
            port=config.port,
            comando=comando
        )
    else:
        follow = '-f' if follow == True else ''
        comando = 'tail {} {}'.format(follow, log_path)
        shellcmd = '{docker_path} exec -it apds{port} {comando}'.format(
            docker_path=config.docker_path,
            port=config.port,
            comando=comando
        )
        subprocess.call(shlex.split(shellcmd))


##########
#  List  #
##########

@click.command()
@pass_config
def list_servers(config):
    '''Lista los servidores en ejecución'''
    click.echo('{:10}{}'.format('PUERTO', 'DIRECTORIO'))
    contenedores = get_running_containers(config.docker_path)
    for contenedor in contenedores:
        if contenedor.strip() == '':
            continue
        nombre, puertos, directorios = contenedor.split('\t')
        if nombre.startswith('apds'):
            puertos = puertos.split(',')
            for puerto in puertos:
                puerto = puerto.strip()
                if puerto.endswith('->80/tcp'):
                    puerto = puerto.split('->80/tcp')[0]
                    puerto = puerto.split(':')[1]
            click.echo('{:10}{}'.format(puerto, directorios))



cli.add_command(start)
cli.add_command(stop)
cli.add_command(restart)

cli.add_command(run)
cli.add_command(logs)
cli.add_command(list_servers, 'list')