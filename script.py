import os
import time
import logging
import threading
from random import randint
from colorama import init, Fore

# ------------------------------------------------------------------------------------------------ #

init(convert=os.name == 'nt')
logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(threadName)s] - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

colors = {
    'repositor': Fore.GREEN,    # color de Repositor
    'proveedor': Fore.YELLOW,   # color de Provedor
    'bebedor': Fore.MAGENTA,    # color de Bebedores
    'reset': Fore.WHITE         # vuelve a poner el color en blanco
}
cantidad = {
    'heladeras': 3
}
frecuencia = {
    'repositor': 2, # frecuencia de entrega de paquetes de cerveza [Segundos]
    'proveedor': 3, # frecuencia de control de heladeras [Segundos]
    'local': 30     # Tiempo que el local esta abierto [Segundos], Si es muy corto los threads no terminan de cumplir sus tareas
}
monitor = {
    'repositor': threading.Condition()
}

# ------------------------------------------------------------------------------------------------ #

class Cerveza:
    def __init__(self, tipo='cerveza'):
        self.tipo = tipo

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
        for x in range( randint(1, 25) ):
            tipo = ('lata' if (randint(0, 10) % 2 == 0) else 'botella')
            self.packDeCervezas.append(Cerveza(tipo))

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
            for heladera in heladeras:
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
        self.reponer('lata', heladera)
        self.reponer('botella', heladera)
        logging.info(f'{colors["repositor"]}REPOSITOR > Heladera[{heladera.id}] llena{colors["reset"]}')

# ------------------------------------------------------------------------------------------------ #

def crearHeladeras():
    heladeras = []
    for i in range(cantidad['heladeras']):
        heladeras.append(Heladera(id=i))
    return heladeras

deposito = Deposito()
heladeras = crearHeladeras()
proveedor = Proveedor()
repositor = Repositor()


localAbierto = True
logging.info(f'LOCAL ABIERTO !')

proveedor.start()
repositor.start()
time.sleep( frecuencia['local'])

localAbierto = False
logging.info(f'LOCAL CERRADO !')

for key in monitor.keys():
    with  monitor[key]:
        monitor[key].notify()