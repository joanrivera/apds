# -*- coding: utf-8 -*-

import click

import os
import subprocess
import shutil
import shlex
import time
import json



def ejecutar_comando(shellcmd, verbose=True):
    p = subprocess.Popen(
        shlex.split(shellcmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    segundos_transcurridos = 0
    if verbose:
        click.echo(' ', nl=False)
    while(True):
        poll = p.poll()
        if poll == None:
            if verbose:
                click.echo('.', nl=False)
            if segundos_transcurridos > 20:
                p.kill()
                if verbose:
                    click.echo(click.style(' Falló', fg='red'))

                return -1
        else:
            if poll != 0:
                if verbose:
                    click.echo(click.style(' Falló', fg='red'))

                    print(p.stdout.read())
                return -1
            if verbose:
                click.echo(click.style(' Ok', fg='green'))

            return 0

        time.sleep(1)

        segundos_transcurridos += 1


def get_running_servers(docker_path, docker_image):
    shellcmd = '{docker_path} ps --no-trunc --format "{{{{.Names}}}}\t{{{{.Ports}}}}\t{{{{.Mounts}}}}" --filter ancestor={docker_image}'.format(
        docker_path=docker_path,
        docker_image=docker_image
    )
    p = subprocess.Popen(shlex.split(shellcmd), stdout=subprocess.PIPE)

    contenedores = p.communicate()[0].split('\n')

    container_data = {}

    for contenedor in contenedores:
        if contenedor.strip() == '':
            continue
        data = contenedor.split('\t')
        nombre = data.pop(0)
        if nombre.startswith('apds'):
            container_data[nombre] = data

    return container_data


def detener_contenedor(docker_path, nombre, verbose=True):
    shellcmd = '{docker_path} rm -f {nombre}'.format(
        docker_path=docker_path,
        nombre=nombre
    )
    ejecutar_comando(shellcmd, verbose)


def obtener_estado_contenedor(docker_path, imagen, nombre):
    '''Comprueba si un contenedor ha sido iniciado'''
    contenedores = get_running_servers(docker_path, imagen)
    ha_sido_iniciado = False
    for name in contenedores:
        if name == nombre:
            ha_sido_iniciado = True

    return ha_sido_iniciado




class Config(object):

    def __init__(self):
        cfg = self.get_conf()
        self.port = cfg['default_port']
        self.docker_path = cfg['docker_path']
        self.docker_image = cfg['docker_image']
        self.dir_maps = cfg['dir_maps']


    def get_conf(self):
        user_ini_path = os.path.expanduser('~/.config/apds.json')
        if not os.path.isfile(user_ini_path):
            cfg = self.get_default_cfg()
            with open(user_ini_path, 'w') as configfile:
                jsondata = json.dumps(cfg, sort_keys=True,
                    indent=4)
                configfile.write(jsondata)
        else:
            jsondata = open(user_ini_path).read()
            cfg = json.loads(jsondata)

        return cfg


    def get_default_cfg(self):
        cfg = {
            'default_port': '8080',
            'docker_image': 'joanrivera/apds:dev',
            'docker_path': '/usr/bin/docker',
            'dir_maps': [],
        }

        return cfg



pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--port', '-p', type=click.INT,
        help='Puerto usado por el servidor')
@pass_config
def cli(config, port):
    '''Apache+PHP Development Server'''
    if port:
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

    iniciado = obtener_estado_contenedor(
        config.docker_path, config.docker_image, 'apds'+str(config.port)
    )

    if iniciado:
        click.echo(click.style('Falló. ', fg='red'), nl=False)
        click.echo(
            'Ya hay un servidor ejecutándose en el puerto {}'.format(config.port)
        )
        exit(1)
    else:
        # Puede ser que hayan restos de servidores que han sido detenidos de
        # forma anormal, por lo que se intentan eliminar explícitamente
        detener_contenedor(config.docker_path, 'apds'+str(config.port), False)

    dir_maps_string = ' '.join(['-v \'{}\''.format(map) for map in config.dir_maps])
    click.echo('Iniciando servidor en puerto %s' % config.port, nl=False)
    droot_expanded = os.path.abspath(os.path.expanduser(document_root))
    shellcmd = '{docker_path} run -d -p {port}:80 -e DOCKER_USER="{username}" -v {document_root}:/var/www/html {dir_maps} --name=apds{port} {docker_image}'.format(
        docker_path=config.docker_path,
        port=config.port,
        dir_maps=dir_maps_string,
        document_root=droot_expanded,
        docker_image=config.docker_image,
        username=os.environ.get('USERNAME')
    )
    ejecutar_comando(shellcmd)


##########
#  Stop  #
##########

@click.command()
@pass_config
def stop(config):
    '''Detiene el servidor'''
    nombre_contenedor = 'apds'+str(config.port)
    iniciado = obtener_estado_contenedor(
        config.docker_path, config.docker_image, nombre_contenedor
    )
    if not iniciado:
        click.echo(click.style('Falló. ', fg='red'), nl=False)
        click.echo(
            'No hay un servidor usando el puerto {}'.format(config.port)
        )
        exit(1)
    click.echo('Deteniendo servidor', nl=False)
    detener_contenedor(config.docker_path, nombre_contenedor)


#############
#  Restart  #
#############

@click.command()
@pass_config
def restart(config):
    '''Reinicia el servidor'''

    iniciado = obtener_estado_contenedor(
        config.docker_path, config.docker_image, 'apds'+str(config.port)
    )

    if not iniciado:
        click.echo(click.style('Falló. ', fg='red'), nl=False)
        click.echo(
            'No hay un servidor ejecutándose en el puerto {}'.format(config.port)
        )
        exit(1)

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
@click.option('--root', is_flag=True,
        help=u'Ejecuta los comandos como root')
@click.argument('comando', nargs=1)
@pass_config
def run(config, root, comando):
    '''Ejecuta un comando que esté disponible dentro del contenedor del servidor'''
    click.echo('Ejecutando: %s' % comando)
    comando='bash -c \'{}\''.format(comando)
    username = 'root'
    if not root:
        username = os.environ.get('USERNAME')
    shellcmd = '{docker_path} exec -it -u={username} apds{port} {comando}'.format(
        docker_path=config.docker_path,
        port=config.port,
        comando=comando,
        username=username
    )
    subprocess.call(shlex.split(shellcmd))


##########
#  Logs  #
##########

@click.command()
@click.option('--follow', '-f', is_flag=True,
        help=u'Muestra las novedades del log según vayan apareciendo')
@click.option('--clear', is_flag=True,
        help=u'Elimina los contenidos del archivo de logs')
@click.option('--no-color', is_flag=True,
        help=u'Muestra los logs sin colores')
@pass_config
def logs(config, follow, clear, no_color):
    '''Muestra el log de errores de PHP'''
    log_path = '/var/log/apache2/error.log'
    if clear:
        comando = 'bash -c "echo \'\' > {}"'.format(log_path)
        shellcmd = '{docker_path} exec -it apds{port} {comando}'.format(
            docker_path=config.docker_path,
            port=config.port,
            comando=comando
        )
        subprocess.call(shellcmd, shell=True)
    else:
        follow = '-f' if follow == True else ''
        colorizer = 'cat' if no_color == True else 'log-colorizer'
        comando = 'bash -c "tail {} {} | {}"'.format(
            follow, log_path, colorizer
        )
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
    contenedores = get_running_servers(config.docker_path, config.docker_image)
    if len(contenedores) > 0:
        click.echo('{:10}{}'.format('PUERTO', 'DIRECTORIO'))
    else:
        click.echo(u'No hay servidores en ejecución')
    for nombre in contenedores.keys():
        puertos, directorios = contenedores[nombre]
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
