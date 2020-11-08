import os
import time
import logging
import threading
from random import randint
from colorama import init , Fore

# ------------------------------------------------------------------------------------------------ #

init(os.name == 'nt')
logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(threadName)s] - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

colors = {
    'repositor': Fore.GREEN,    # color de Repositor
    'proveedor': Fore.YELLOW,   # color de Provedor
    'bebedor': Fore.MAGENTA,    # color de Bebedores
    'reset': Fore.WHITE         # vuelve a poner el color en blanco
}
cantidad = {
    'heladeras': 3,
    'bebedores': 5
}
frecuencia = {
    'repositor': 2, # frecuencia de entrega de paquetes de cerveza [Segundos]
    'proveedor': 3, # frecuencia de control de heladeras [Segundos]
    'bebedor': 2,   # frecuencia de consumo de cerveza de los clientes [Segundos]
    'local': 60     # Tiempo que el local esta abierto [Segundos], Si es muy corto los threads no terminan de cumplir sus tareas
}
monitor = {
    'repositor': threading.Condition(),
    'bebedores': threading.Condition()
}
semaforoBebedores = threading.Semaphore(cantidad['bebedores'])

# ------------------------------------------------------------------------------------------------ #

class Cerveza:
    def __init__(self, tipo='cerveza', pinchada=False):
        self.tipo = tipo
        self.pinchada = pinchada

class PackDeCervezas:
    def __init__(self):
        self.cervezas= []

    def set(self, listaDeCervezas):
        self.cervezas = listaDeCervezas

    def get(self):
        return self.cervezas
    
    def getTipos(self):
        return list(map(lambda cerveza: cerveza.tipo ,self.cervezas))

    def append(self, unaCerveza):
        self.cervezas.append(unaCerveza)
    
    def clear(self):
        self.cervezas.clear()

    def remove(self, unTipoDeCerveza):
        return self.cervezas.pop( self.getTipos().index(unTipoDeCerveza))

    def pop(self, index = 0):
        return self.cervezas.pop( index )

    def size(self):
        return len(self.cervezas)

    def contains(self, unTipoDeCerveza):
        return unTipoDeCerveza in self.getTipos()
    
    def count(self, unTipoDeCerveza):
        return self.getTipos().count(unTipoDeCerveza)

# ------------------------------------------------------------------------------------------------ #

class Deposito:
    def __init__(self):
        self.cervezas = PackDeCervezas()

    def colocar(self, packDeCervezas):
        for cerveza in packDeCervezas.cervezas:
            self.cervezas.append( cerveza )

    def sacar(self, unTipoDeCerveza):
        return self.cervezas.remove( unTipoDeCerveza ) if (self.cervezas.contains(unTipoDeCerveza)) else False

# ------------------------------------------------------------------------------------------------ #

class Heladera(Deposito):
    def __init__(self, capacidadLatas=15, capacidadBotellas=10, id=0):
        super().__init__()
        self.id = id
        self.capacidad = {'lata': capacidadLatas,'botella': capacidadBotellas}
        self.enchufada = False
        self.enfriadoRapido = False
    
    def colocar(self, unaCerveza):
        if( self.hayEspacioPara(unaCerveza.tipo) ):
            self.cervezas.append( unaCerveza )

    def hayEspacioPara(self, unTipoDeCerveza):
        return self.cervezas.count(unTipoDeCerveza) < self.capacidad[unTipoDeCerveza]

    def espaciosPara(self, unTipoDeCerveza):
        return self.capacidad[unTipoDeCerveza] - self.cervezas.count(unTipoDeCerveza)
    
    def estaLlena(self):
        return self.cervezas.size() == (self.capacidad['lata'] + self.capacidad['botella'])

# ------------------------------------------------------------------------------------------------ #

class Proveedor(threading.Thread):
    def __init__(self):
        super().__init__()
        self.packDeCervezas = PackDeCervezas()

    def run(self):
        global localAbierto, frecuencia
        while localAbierto:
            self.producirCervezas()
            self.entregar()
            time.sleep( frecuencia['proveedor'] )

    def entregar(self):
        global monitor, deposito
        with monitor['repositor']:
            deposito.colocar(self.packDeCervezas)
            monitor['repositor'].notify()
        logging.info(f'{colors["proveedor"]}PROVEEDOR > Entregue un paquete de {self.packDeCervezas.size()} cervezas{colors["reset"]}')
        self.packDeCervezas.clear()

    def producirCervezas(self):
        for x in range( randint(1, 30) ):
            tipo = ('lata' if (randint(0, 10) % 2 == 0) else 'botella')
            pinchada = (False if ( tipo=='botella' or randint(0, 25) % 5 != 0) else True)
            self.packDeCervezas.append( Cerveza(tipo, pinchada) )

# ------------------------------------------------------------------------------------------------ #

class Repositor(threading.Thread):
    def __init__(self):
        super().__init__()
        self.cervezas = PackDeCervezas()

    def run(self):
        global heladeras

        for heladera in heladeras:
            heladera.enchufada = True
            self.llenar(heladera)
            heladera.enfriadoRapido = True
        self.controlarHeladeras()

    def controlarHeladeras(self):
        global localAbierto, heladeras
        while localAbierto:
            with monitor['bebedores']:
                monitor['bebedores'].notify()
            for heladera in heladeras:
                self.quitarPinchadas(heladera)
                if not heladera.estaLlena():
                    self.llenar(heladera)
            time.sleep(frecuencia['repositor'])

    def traerCervezas(self, unTipoDeCerveza, cantidad):
        global monitor, deposito
        for x in range(cantidad):
            cervezaDelDeposito = deposito.sacar(unTipoDeCerveza)
            with monitor['repositor']:
                while not(cervezaDelDeposito) and localAbierto:
                    logging.info(f'{colors["repositor"]}REPOSITOR > Sin stock de {unTipoDeCerveza}s para reponer, esperando proveedor...{colors["reset"]}')
                    monitor['repositor'].wait()
                    cervezaDelDeposito = deposito.sacar(unTipoDeCerveza)
                self.cervezas.append(cervezaDelDeposito)

    def reponer(self, unTipoDeCerveza, unaHeladera):
        while unaHeladera.hayEspacioPara(unTipoDeCerveza):
            if self.cervezas.contains(unTipoDeCerveza):
                unaHeladera.colocar( self.cervezas.remove(unTipoDeCerveza) )
            else:
                self.traerCervezas( unTipoDeCerveza, unaHeladera.espaciosPara(unTipoDeCerveza) )
    
    def llenar(self, heladera):
        self.reponer('botella', heladera)
        self.reponer('lata', heladera)
        logging.info(f'{colors["repositor"]}REPOSITOR > Heladera[{heladera.id}] llena{colors["reset"]}')
    
    def quitarPinchadas(self, heladera):
        heladera.cervezas.set(list(filter(lambda cerveza: not(cerveza.pinchada), heladera.cervezas.get())))
        if heladera.espaciosPara('lata') != 0:
            logging.info(f'{colors["repositor"]}REPOSITOR > {heladera.espaciosPara("lata")} latas pinchadas sacadas de Heladera[{heladera.id}]{colors["reset"]}')

# ------------------------------------------------------------------------------------------------ #

class Bebedor(threading.Thread):
    def __init__(self, cervezasQueToma='cerveza', limite=0, id=0):
        super().__init__()
        self.id = id
        self.limite = limite
        self.cervezasTomadas = 0
        self.cervezasQueToma = cervezasQueToma

    def run(self):
        global frecuencia, heladeras,monitor

        with monitor['bebedores']:
            monitor['bebedores'].wait()     # Esopera que el repositor llene las heladeras 

        while self.cervezasTomadas < self.limite and localAbierto:
            self.tomarCerveza( self.elegirHeladera( heladeras ) )
            if self.cervezasTomadas == self.limite:
                logging.info(f'{colors["bebedor"]}BEBEDOR[{self.id}] > No puedo tomar más, me voy a dormir...{colors["reset"]}')
            time.sleep(frecuencia['bebedor'])
    
    def tomarCerveza(self, heladera):
        global monitor
        cerveza = self.elegirCerveza(heladera)
        with monitor['bebedores']:
            while not(cerveza) and localAbierto:
                logging.info(f'{colors["bebedor"]}BEBEDOR[{self.id}] > No hay {self.cervezasQueToma}s en la heladera[{heladera.id}], esperando repositor...{colors["reset"]}')
                monitor['bebedores'].wait()
                cerveza = self.elegirCerveza(heladera)
        if cerveza.pinchada:
            logging.info(f'{colors["bebedor"]}BEBEDOR[{self.id}] > Saque una lata pinchada de la heladera[{heladera.id}], Voy a sacar otra...{colors["reset"]}')
            self.tomarCerveza(heladera)
        else:
            self.cervezasTomadas += 1
            logging.info(f'{colors["bebedor"]}BEBEDOR[{self.id}] > Me tome una {self.cervezasQueToma}, llevo tomadas {self.cervezasTomadas} cervezas y puedo tomar hasta {self.limite}...{colors["reset"]}')
    
    def elegirCerveza(self, heladera):
        if self.cervezasQueToma == 'cerveza':
            return heladera.sacar( 'lata' if (randint(0, 10) % 2 == 0) else 'botella')
        else:
            return heladera.sacar(self.cervezasQueToma)

    def elegirHeladera(self, listaDeHeladeras):
        return listaDeHeladeras[ randint(0, len(listaDeHeladeras)-1) ]

# ------------------------------------------------------------------------------------------------ #

def crearHeladeras():
    heladeras = []
    for i in range(cantidad['heladeras']):
        heladeras.append(Heladera(id=i))
    return heladeras

def crearBebedores():
    bebedores = []
    for i in range(cantidad['bebedores']):
        limite = randint(1, 10)
        opcion = randint(1, 30) % 3
        if opcion == 0:
            cervezasQueToma = 'botella'
        elif opcion == 1:
            cervezasQueToma = 'lata'
        else:
            cervezasQueToma = 'cerveza'
        bebedores.append( Bebedor(cervezasQueToma, limite, i))
    return bebedores

# ------------------------------------------------------------------------------------------------ #

deposito = Deposito()
heladeras = crearHeladeras()
proveedor = Proveedor()
repositor = Repositor()
bebedores = crearBebedores()

localAbierto = True
logging.info(f'LOCAL ABIERTO !')

proveedor.start()
repositor.start()
for beberor in bebedores:
    beberor.start()
time.sleep( frecuencia['local'])

localAbierto = False
logging.info(f'LOCAL CERRADO !')


for key in monitor.keys():
    with  monitor[key]:
        monitor[key].notify()
