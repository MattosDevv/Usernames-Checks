# Discord Username Checker
Ferramenta para verificar disponibilidade de usernames no Discord, com suporte a proxies, ScraperAPI e notificações via webhook.



## Requisitos

- Python 3.8+
- Instalar dependências:

```bash
pip install requests colorama
```



## Configuração

### 1. `key.txt` (obrigatório se usar proxy ou ScraperAPI)

Crie um arquivo `key.txt` na mesma pasta do script(OBS: Ja disponibilizei uma pra uso). Coloque uma entrada por linha:

```
# Chaves ScraperAPI (32 caracteres hex)
a1b2c3d4e1b2c3d4e1b2c3d4e1b2c3d4

# Proxies (formato user:pass@host:port ou host:port)
usuario:senha@192.168.0.1:8080
192.168.0.2:3128
```

Linhas começando com `#` são ignoradas.




## Como usar

```bash
python users.py
```

Ao iniciar, o script vai pedir o seu **Discord Webhook URL** para receber notificações de usernames disponíveis. Deixe em branco para desativar.


## Cache

Os resultados são salvos automaticamente em `checked_users.json` para evitar verificar o mesmo username duas vezes entre sessões.

---

