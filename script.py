import time
import logging
import threading
import random

# ------------------------------------------------------------------------------------------------ #

logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(threadName)s] - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)
monitor = threading.Condition()
heladeras = []
ctdHeladeras = 3
localAbierto = True
frecuencia = {
    'repositor': 2, # frecuencia de entrega de paquetes de cerveza [Segundos]
    'proveedor': 3, # frecuencia de control de heladeras [Segundos]
    'bebedor': 1,    # frecuencia de consumo de cerveza de los clientes [Segundos]
    'local': 20 # Tiempo que el local esta abierto [Segundos]
}

# ------------------------------------------------------------------------------------------------ #

class Cerveza:
    def __init__(self, tipo='cerveza', pinchada=False):
        self.tipo = tipo
        self.pinchada = pinchada

class PackDeCervezas:
    def __init__(self):
        self.cervezas= []
    
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
        global monitor
        with monitor:
            while not(self.cervezas.contains(unTipoDeCerveza)) and (localAbierto):
                self.sinStock(unTipoDeCerveza)
                monitor.wait()
        return self.cervezas.remove( unTipoDeCerveza )

    def sinStock(self, unTipoDeCerveza):
        logging.info(f'REPOSITOR > Sin stock de {unTipoDeCerveza}s para reponer, esperando proveedor...')

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

    def sinStock(self, unTipoDeCerveza):
        logging.info(f'Heladera [{self.id}] sin {unTipoDeCerveza}s, esperando repositor...')

    def hayEspacioPara(self, unTipoDeCerveza):
        return self.cervezas.count(unTipoDeCerveza) < self.capacidad[unTipoDeCerveza]

    def espaciosPara(self, unTipoDeCerveza):
        return self.capacidad[unTipoDeCerveza] - self.cervezas.count(unTipoDeCerveza)
    
    def estaLlena(self):
        return self.cervezas.size() == (self.capacidad['lata'] + self.capacidad['botella'])

# ------------------------------------------------------------------------------------------------ #

class Proveedor(threading.Thread):
    def __init__(self, unDeposito):
        super().__init__()
        self.packDeCervezas = PackDeCervezas()
        self.depositoCliente = unDeposito

    def run(self):
        global localAbierto, frecuencia
        while localAbierto:
            self.producirCervezas()
            self.entregarA(self.depositoCliente)
            time.sleep( frecuencia['proveedor'] )

    def entregarA(self, unDeposito):
        global monitor
        with monitor:
            unDeposito.colocar(self.packDeCervezas)
            monitor.notify()
        logging.info(f'PROVEEDOR > Entregue un paquete de {self.packDeCervezas.size()} cervezas')
        self.packDeCervezas.clear()

    def producirCervezas(self):
        for x in range( random.randint(1, 25) ):
            nuevaCerveza = Cerveza(
                tipo = ('lata' if (random.randint(0, 10) % 2 == 0) else 'botella'),
                pinchada = (True if (random.randint(0, 25) % 5 == 0) else False)
            )
            self.packDeCervezas.append(nuevaCerveza)

# ------------------------------------------------------------------------------------------------ #

class Repositor(threading.Thread):
    def __init__(self, unDeposito, heladeras):
        super().__init__()
        self.cervezas = PackDeCervezas()
        self.deposito = unDeposito
        self.heladeras = heladeras

    def run(self):
        for heladera in self.heladeras:
            heladera.enchufada = True
            self.llenar(heladera)
            heladera.enfriadoRapido = True
        self.controlarHeladeras()

    def controlarHeladeras(self):
        global localAbierto
        while localAbierto:
            for heladera in self.heladeras:
                if not heladera.estaLlena():
                    self.llenar(heladera)
            time.sleep(frecuencia['repositor'])

    def traerCervezas(self, unTipoDeCerveza, cantidad):
        for x in range(cantidad):
            self.cervezas.append( self.deposito.sacar(unTipoDeCerveza) )

    def reponer(self, unTipoDeCerveza, unaHeladera):
        while unaHeladera.hayEspacioPara(unTipoDeCerveza):
            if self.cervezas.contains(unTipoDeCerveza):
                unaHeladera.colocar( self.cervezas.remove(unTipoDeCerveza) )
            else:
                self.traerCervezas( unTipoDeCerveza, unaHeladera.espaciosPara(unTipoDeCerveza) )
    
    def llenar(self, heladera):
        self.reponer('lata', heladera)
        self.reponer('botella', heladera)
        logging.info(f'REPOSITOR > Heladera[{heladera.id}] llena')

# ------------------------------------------------------------------------------------------------ #

for i in range(ctdHeladeras):
    heladeras.append(Heladera(id=i))

deposito = Deposito()
proveedor = Proveedor( deposito )
repositor = Repositor( deposito, heladeras )

logging.info(f'LOCAL ABIERTO !')
proveedor.start()
repositor.start()

time.sleep( frecuencia['local'])
localAbierto = False
logging.info(f'LOCAL CERRADO !')

with monitor:
    monitor.notify()
