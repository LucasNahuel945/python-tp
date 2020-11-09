Esta solución requiere la instalacion del modulo colorama el cual sirve para utilizar colores en la terminal de una manera más sencilla. 

~~~
pip install colorama
~~~

---

# Python TP
Somos los encargados de organizar una fiesta, y se nos encomendó llenar las heladeras de cerveza.

Cada heladera tiene capacidad para 10 botellas  y 15 latas. Las latas no pueden ser
ubicadas en el sector de las botellas y viceversa.

Para no confundirnos, las heladeras hay que llenarlas de a una y en orden. Hasta no llenar completamente
una heladera (ambos tipos de envases), no pasamos a la siguiente. Además, debemos enchufarlas antes
de empezar a llenarlas. Una vez llena, hay que presionar el botón de enfriado rápido.

Al bar llegan los proveedores y nos entregan cervezas al azar, tanto en cantidad como en tipo de envase. 

## Bonus
1. Agregar beodes que consumen todo el tiempo cervezas.
	* Consumen cada vez 1 cerveza de una heladera al azar, y si esa heladera no tiene lo que quieren, se queda esperando.
	* Hay beodes de diferentes gustos, algunes solamente consumen botellas, otres solamente latas, y otres ambos tipos de envase. 
	* Cada beode tiene un límite de consumo, luego del cual se desmaya y deja de consumir.
	* Seguimos llenando las heladeras en el orden original, y  hasta no llenar completamente una heladera (ambos tipos de envases), no pasamos a la siguiente.
1. Agregar que cada tanto nos damos cuenta de alguna lata que está pinchada en alguna heladera, y por lo tanto hay que sacar esa lata de esa heladera.
1. Dado los anteriores dos ítems, con beodes y latas que se pinchan, las heladeras pueden quedar llenas, medio llenas o vacías, pero en diferente orden al original.
	* Hacer que las heladeras, al llegar los proveedores, se vayan llenando en orden de prioridad de acuerdo a lo vacías que estén. Es decir primero las vacías, luego las que tienen 1 cerveza (botella o lata), luego las que tienen dos cervezas (en total botellas+latas), etc.
	* Cuidado, al llegar los proveedores, para decidir el orden de prioridad de llenado de las heladeras, no hay que permitir que se saquen cervezas (por consumo, por pinchadura, o lo que sea).
	* Como siempre, hasta no llenar completamente una heladera (ambos tipos de envases), no pasamos a la siguiente.
1. En el anterior ítem al llegar un proveedor, por un tema de cantidad de cervezas de cada envase, puede no servir para llenar la heladera primera en orden de prioridad a ser llenada.
	* Agregar la posibilidad de poder pasar a las siguientes heladeras a ser llenadas, respetando el orden de prioridad del punto anterior.
	* Ejemplo: la primera heladera a ser llenada le faltan 3 botellas y 10 latas, pero el proveedor cae con 5 botellas y 6 latas. Entonces las 2 botellas restantes meterlas en la siguiente heladera en la que haya lugar, respetando el orden de prioridad del ítem anterior.
