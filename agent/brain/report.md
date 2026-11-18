## 1.2 C и Python вместе

Собрать ядро на C в динамическую библиотеку и вызвать его из Python через ctypes.

Собрал ядро из 1.1 в динамическую библиотеку `sentry_core.dll`. Подключил её через `ctypes`, проверил раскладку структуры и обработку ошибки пустого указателя. Python формирует событие `agent_started` в JSON.

Запуск из папки `agent/` на Windows (в среде x64 Native Tools Command Prompt for VS 2022):

```cmd
cl /nologo /W4 /LD core/core_info.c /Fe:core/sentry_core.dll
dumpbin /nologo /exports core/sentry_core.dll
py brain/brain.py --layout
py brain/brain.py --check-null
py brain/brain.py
```

```text
1.2 · Журнал проверки

sizeof: 272, offsets: 0 8 12 16
NULL: 87 (Параметр задан неверно.)
{"event": "agent_started", "os": "win32", "pid": 14820, "cpus": 16, "page_size": 4096, "host": "DESKTOP-1JEF7SJ"}
1    0 00001000 core_get_info
```
