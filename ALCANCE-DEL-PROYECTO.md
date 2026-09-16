# FUDO Plus — Definición del proyecto y alcance del MVP

## Problema

Los negocios de comida pierden ventas, demoran la atención y cometen errores cuando dependen de llamadas, mensajes de WhatsApp o de tomar los pedidos manualmente. Esto dificulta organizar los pedidos y atender a más clientes.

## Usuarios

1. **Cliente final:** consulta el menú y realiza un pedido online.
2. **Dueño o personal del negocio:** carga productos, recibe pedidos y consulta su estado.

El MVP se probará con **un único negocio**. La posibilidad de incorporar muchos negocios en una misma plataforma queda para una etapa posterior.

## Beneficio esperado

FUDO Plus busca centralizar la venta online, reducir errores en los pedidos y hacer más sencilla la operación diaria del negocio.

## Qué incluye el MVP

- Acceso del negocio al sistema.
- Carga y publicación de productos con nombre, descripción, foto, precio y disponibilidad.
- Menú público accesible mediante un enlace.
- Carrito con productos y cantidades.
- Pedido para **delivery o retiro en el local**.
- Ubicación o referencia escrita por el cliente cuando sea necesaria.
- Elección entre **pago en efectivo o pago dentro de la aplicación/sistema**.
- Intento de integración real con Mercado Pago.
- Si la integración real no llega a tiempo, flujo de pago simulado claramente identificado.
- Recepción del pedido por parte del negocio como ticket con productos, cantidades, total, modalidad, ubicación y estado del pago.
- Opción simple para marcar un producto como disponible o sin stock.

## Qué queda fuera del MVP

- Pedidos desde mesas o códigos QR.
- Integración con Voy Yo.
- Puntos, cupones o programas de fidelización.
- Multitenancy, múltiples negocios, sucursales o franquicias.
- Gestión avanzada de inventario en tiempo real.
- Pedidos programados para otro momento.
- Cierre de caja, contabilidad y reportes avanzados.
- Aplicación móvil nativa.

## Criterio de éxito

Un negocio de prueba debe poder publicar productos desde el sistema y un cliente debe poder completar un pedido para delivery o retiro. El negocio debe recibir un ticket con los datos y precios correctos, y el pedido debe indicar si el pago fue en efectivo, aprobado, rechazado o simulado.

## Decisiones pendientes

- Confirmar con un negocio si necesita cantidades de stock o solo la marca “disponible/sin stock”.
- Confirmar con David la forma más sencilla de probar Mercado Pago sin poner claves en el código.
- Registrar por escrito la aprobación final del alcance por parte del Product Owner.
