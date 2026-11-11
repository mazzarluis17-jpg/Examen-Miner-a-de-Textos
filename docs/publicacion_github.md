# Publicación personal y entrega del enlace

**Preparación, no publicación realizada.** No se ha añadido un destino GitHub ni
se ha hecho push. Primero Luis debe revisar la URL de su cuenta y autorizarla.
No reutilizar el GitLab del profesor como destino de entrega.

Después de aprobar los tres cortes del reporte, láminas y guion, realizar un
ensayo real de ocho minutos o menos y completar la reconstrucción e integridad:

1. Crear en la cuenta personal un repositorio GitHub vacío, sin README ni licencia
   autogenerados para evitar una historia ajena. Elegir público o conceder acceso
   explícito al profesor si es privado. No publicar los Excel auxiliares.
2. Verificar `git status --short`, `git branch --show-current` y
   `git remote -v`. La rama de entrega es desarrollo-luis; conservar origin.
3. Solo después de revisar y autorizar el destino, ejecutar estas órdenes,
   sustituyendo TU_USUARIO por el usuario real:

```bash
git remote add github https://github.com/TU_USUARIO/text-mining-ir-er.git
git remote get-url github
git push -u github desarrollo-luis
git push github reglas-congeladas
```

4. Configurar desarrollo-luis como rama predeterminada en GitHub. Verificar desde
   una sesión con los permisos del profesor que se abren los seis CSV raíz, el
   reporte final y las láminas. Registrar fecha/hora real y acceso comprobado.
5. Crear la etiqueta final solamente cuando se satisfagan las condiciones del PRD:

```bash
git tag -a v1.0-entrega -m "Examen 1 de Minería de Textos: entrega final"
git push github v1.0-entrega
```

No recrear etiquetas existentes ni sobrescribir el historial. Entregar el enlace
`https://github.com/TU_USUARIO/text-mining-ir-er` y el hash del commit evaluable,
antes de las 20:00 del 11 de noviembre de 2026, hora de México. Estos comandos
requieren la autorización de publicación que todavía no ha sido emitida.
