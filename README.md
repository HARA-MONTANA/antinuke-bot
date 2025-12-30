# antinuke-bot

Bot de seguridad para Discord enfocado en mitigar raids, intentos de nuke y estafas. Este documento explica cómo funciona el código de `omega.py` y cómo configurarlo.

## Requisitos
- Python 3.9+.
- Dependencias de PyPI:
  - [`discord.py`](https://pypi.org/project/discord.py/)
  - [`textdistance`](https://pypi.org/project/textdistance/)

Instala las dependencias con:

```bash
pip install discord.py textdistance
```

## Configuración
Edita los valores de `OmegaConfig` en `omega.py`:

- `TOKEN`: token del bot de Discord.
- `LOG_CHANNEL_ID`: ID del canal donde se enviarán los reportes y alertas.
- `LOG_INTERVAL_HOURS`: intervalo (en horas) para los reportes automáticos al canal de logs.
- `PREFIX`: prefijo de comandos (por defecto `"dose"`). Puedes cambiarlo en caliente con el comando `dose set_prefix`.
- `CONFIG_PREFIX_COMMAND`: prefijo fijo que **siempre** usará el comando `set_prefix` para permitir restaurar el prefijo en caso de
  haberlo configurado mal. Por defecto también es `"dose"`.
- `SAFE_DOMAINS`: dominios permitidos; se usa para detectar phishing por similitud.
- Límites y umbrales de seguridad:
  - `MAX_MENTIONS_LIMIT`: menciones permitidas por mensaje antes de considerarse spam.
  - `SPAM_MESSAGE_LIMIT`, `SPAM_WINDOW_SECONDS`, `SPAM_TIMEOUT_MINUTES`: controlan cuántos mensajes en pocos segundos disparan el
    anti-spam y la duración del timeout automático. Puedes cambiarlos en caliente con comando.
  - `BURST_JOIN_LIMIT` / `BURST_JOIN_WINDOW`: número de usuarios que pueden unirse en una ventana de tiempo (segundos) antes de activar modo lockdown. También puedes modificarlos en caliente con comandos.
  - `MIN_ACCOUNT_AGE_DAYS`: edad mínima de cuenta para permitir la entrada. Puedes ajustarla en caliente con comando.
  - `MAX_CHANNEL_DELETIONS`, `MAX_ROLE_DELETIONS`, `MAX_MEMBER_KICKS`: umbrales de acciones administrativas antes de retirar roles al sospechoso.

## Puesta en marcha
1. Configura los valores anteriores.
2. Ejecuta el bot:

```bash
python omega.py
```

Cuando el bot se conecte, enviará un embed de estado al canal configurado en `LOG_CHANNEL_ID` y arrancará el reseteo periódico del conteo de acciones administrativas.
Los reportes automáticos de estado se enviarán al canal de logs siguiendo el intervalo definido en `LOG_INTERVAL_HOURS` o por el comando `dose set_log_channel`.

## Cómo funciona la protección
- **Anti-phishing:** analiza URLs en mensajes de usuarios sin permisos de administrador. Si la similitud con un dominio seguro está entre 0.75 y 1.0 (Levenshtein normalizado), borra el mensaje, banea al usuario y suma al contador `phishing`.
- **Anti-spam:** si un usuario sin permisos de administrador envía 6 mensajes o más en 3 segundos, se borran sus mensajes recientes y recibe automáticamente un timeout de 30 minutos. El contador `spam` aumenta y se registra en el canal de logs.
- **Anti-alt:** baneos automáticos de cuentas con menos días que `MIN_ACCOUNT_AGE_DAYS` al unirse.
- **Detección de raids:** si se unen `BURST_JOIN_LIMIT` usuarios en menos de `BURST_JOIN_WINDOW` segundos, activa `lockdown`, deshabilitando permisos de escribir para `@everyone` y aumenta el contador `raids`.
- **Protección anti-nuke:** monitoriza el registro de auditoría por eliminaciones de canales/roles y expulsiones. Si un administrador supera los límites configurados, se le retiran todos los roles mediante `neutralize_admin` y se incrementa `nuke_attempts`.

Los contadores y el estado de `lockdown` se mantienen en memoria desde el arranque del bot.

## Comandos disponibles
> El prefijo de comandos es configurable en `OmegaConfig.PREFIX` y puede cambiarse en caliente. Los ejemplos usan `dose`, pero puedes usar el prefijo que tengas activo. Solo administradores pueden usarlos.

- `dose report`: muestra uptime, cantidad de ataques anti-nuke, raids detenidas, eventos de phishing y si el modo lockdown está activo. También funciona con el prefijo que hayas configurado (p. ej. `!report`).
- `dose disengage`: desactiva el modo lockdown y restaura los permisos básicos de `@everyone` (enviar mensajes, conectarse y reaccionar).
- `dose set_prefix <nuevo_prefijo>`: cambia el prefijo para **todos** los comandos (p. ej. `!report`). Este comando **siempre** debe
  ejecutarse con el prefijo fijo definido en `CONFIG_PREFIX_COMMAND` (por defecto `dose`), aunque hayas cambiado el prefijo general.
- `dose set_log_channel <#canal> <horas>`: define el canal de logs y cada cuánto (en horas) se enviará el reporte automático de estado.
- `dose set_spam <limite_mensajes> <ventana_segundos> <timeout_minutos>`: ajusta en caliente el umbral anti-spam y la duración del timeout.
- Ajuste de umbrales en caliente (solo admins):
  - `dose set_min_age <dias>`: cambia `MIN_ACCOUNT_AGE_DAYS` y responde tanto con `dose` como con el prefijo configurado.
  - `dose set_burst_limit <usuarios>`: cambia `BURST_JOIN_LIMIT` y responde tanto con `dose` como con el prefijo configurado.
  - `dose set_burst_window <segundos>`: cambia `BURST_JOIN_WINDOW` y responde tanto con `dose` como con el prefijo configurado.
  - Todos los parámetros deben ser enteros; los valores negativos no son aceptados.

## Consejos operativos
- Asigna `LOG_CHANNEL_ID` a un canal privado de staff para no exponer alertas.
- Comprueba que el bot tenga permisos para gestionar roles, canales y baneos; de lo contrario, algunas acciones de mitigación pueden fallar silenciosamente.
- Ajusta los umbrales según el tamaño y actividad habitual de tu servidor para reducir falsos positivos.
