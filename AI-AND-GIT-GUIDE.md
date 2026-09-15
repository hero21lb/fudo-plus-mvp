# Guía de trabajo para el equipo y las IAs

Este documento explica cómo colaborar en FUDO Plus sin pisar el trabajo de otra persona. Las IAs pueden ayudar a escribir código, documentación, pruebas y diagramas, pero cada cambio debe ser revisado por una persona del equipo.

## Regla principal

`main` contiene únicamente versiones estables. `develop` reúne el trabajo aprobado para la próxima versión. Nadie trabaja directamente sobre esas dos ramas.

Cada historia o tarea tiene su propia rama, creada desde `develop`.

## Cómo empezar una tarea

1. Revisar la tarjeta de Trello y confirmar qué debe entregar.
2. Actualizar la copia local de `develop`.
3. Crear una rama nueva con un nombre claro:

```text
feature/US-04-prototipo-minimo
docs/US-03-vision-alcance
fix/US-04-error-inicio
```

4. Trabajar solamente en esa rama.
5. Hacer cambios pequeños y guardarlos en commits separados.
6. Después de cada cambio pequeño y comprobado, hacer commit y push de la rama para dejar una copia respaldada y visible para el equipo.
7. Abrir una solicitud de revisión hacia `develop` cuando la tarea esté lista.

## Antes de empezar a programar

Actualizar la rama base para reducir conflictos:

```bash
git switch develop
git pull origin develop
git switch -c feature/US-XX-nombre-corto
```

Si la rama ya existe:

```bash
git switch feature/US-XX-nombre-corto
git fetch origin
git rebase origin/develop
```

Si todavía no tienen repositorio remoto, pueden omitir `origin` y trabajar con las ramas locales.

## Reglas para las IAs

Antes de pedir código a una IA, indicar:

- qué historia de usuario se está trabajando;
- qué archivos puede modificar;
- qué archivos no debe tocar;
- qué criterios de aceptación debe cumplir;
- cómo se comprobará el resultado.

Después de recibir una propuesta de la IA:

- revisar cada cambio;
- comprobar que no haya secretos, contraseñas ni claves de pago;
- ejecutar la aplicación o las pruebas correspondientes;
- verificar que no haya cambios ajenos a la tarea;
- explicar en el commit qué se modificó.

La IA no debe crear ramas, hacer merges, borrar trabajo ni cambiar archivos de otra historia sin autorización explícita del responsable.

## Cómo evitar conflictos

- No trabajar dos personas sobre los mismos archivos si se puede dividir la tarea.
- No reformatear todo el proyecto en una rama que solo cambia una función.
- No mezclar cambios de varias historias en un mismo commit.
- Integrar cambios pequeños y con frecuencia.
- Avisar en Trello si dos tareas necesitan modificar el mismo archivo.
- No subir archivos locales, claves, contraseñas ni `.env`.
- Mantener los commits pequeños y descriptivos.

Ejemplos:

```text
feat: agrega endpoint de productos
docs: explica cómo iniciar el proyecto
fix: valida precio vacío en formulario
```

Después de un cambio comprobado:

```bash
git add archivo-cambiado
git commit -m "tipo: describe el cambio"
git push
```

No esperen a terminar toda la historia para subir el trabajo. Los commits deben representar avances reales y entendibles; no hace falta crear un commit por cada línea modificada.

## Antes de abrir una solicitud de revisión

```bash
git status
git diff --check
git fetch origin
git rebase origin/develop
```

Luego ejecutar la comprobación correspondiente, revisar los archivos cambiados y subir la rama:

```bash
git push -u origin feature/US-XX-nombre-corto
```

La solicitud debe indicar:

- qué problema resuelve;
- qué archivos cambió;
- cómo se probó;
- qué queda pendiente, si algo no pudo terminarse.

## Si aparece un conflicto

1. No borrar archivos ni aceptar todos los cambios automáticamente.
2. Avisar en el grupo y marcar la tarjeta como bloqueada si impide avanzar.
3. Abrir los archivos con marcas de conflicto y decidir qué versión representa mejor la tarea.
4. Pedir ayuda al responsable de la otra rama si el conflicto mezcla decisiones de producto.
5. Después de resolverlo, comprobar la aplicación y revisar el diff completo.
6. Continuar el rebase:

```bash
git add archivo-resuelto
git rebase --continue
```

Si la resolución salió mal y todavía no se confirmó, volver atrás:

```bash
git rebase --abort
```

## Revisión y merge

- El autor no aprueba su propia solicitud.
- Cada solicitud necesita al menos una revisión de otra persona.
- La rama se integra a `develop` solo cuando cumple la tarjeta y la revisión.
- `main` se actualiza únicamente para una entrega estable o demo aprobada.
- Después del merge, eliminar la rama remota y local si ya no se necesita.

## Distribución recomendada de revisiones

- Cambios de arquitectura, base de datos o pagos: Nahuel revisa.
- Infraestructura y puesta en marcha: David revisa con Nahuel cuando haga falta.
- Visión, flujo y textos de usuario: Exequiel valida.
- Interfaz, documentación y QA manual: Agustin y Joaquin trabajan en pareja.
- Juan Cruz participa como revisor puntual cuando esté disponible.

La prioridad es integrar cambios pequeños, entendibles y comprobados. La velocidad importa menos que poder explicar qué cambió y por qué.
