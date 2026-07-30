import requests
import time
import random
import json
import os

from typing import Dict, List, Optional
from datetime import datetime

import itertools
import string

try:
    from colorama import init, Fore, Style

    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

    class Fore:
        MAGENTA = ""
        LIGHTMAGENTA_EX = ""
        LIGHTBLACK_EX = ""
        YELLOW = ""
        RED = ""
        GREEN = ""
        CYAN = ""
        RESET = ""


def center_text(text):
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80
    return "\n".join(line.center(terminal_width) for line in text.splitlines())


def mostrar_banner():
    banner = (
        f"{Fore.MAGENTA}\n"
        " _    _                     \n"
        "| |  | |                    \n"
        "| |  | |___  ___ _ __ ___   \n"
        r"| |  | / __|/ _ \ '__/ __|  " + "\n"
        r"| |__| \__ \  __/ |  \__ \  " + "\n"
        r" \____/|___/\___|_|  |___/" + "\n"
        f" {Fore.LIGHTMAGENTA_EX}         Discord Username Checker - MattosDev {Fore.RESET}\n"
        f" {Fore.LIGHTBLACK_EX}                                \n"
    )
    print(center_text(banner))


class WebhookManager:
    """Webhooks para notificaçoes de resultados"""

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)

    def send_notification(self, title: str, message: str, color: int = 3447003):
        """Envia notificação via webhook"""
        if not self.enabled:
            return False

        embed = {
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Discord Username Checker",
            }
        }

        payload = {
            "embeds": [embed]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 204
        except Exception as e:
            print(f"{Fore.RED}Erro ao enviar ao webhook: {e}")
            return False

    def send_available_username(self, username: str, details: str):
        """Envia notificaçao de username disponivel"""
        message = f"**Username:** `{username}`\n**Status:** {details}"
        return self.send_notification("Username Disponivel!", message, 778899)  

    def send_script_start(self, mode: str, total_checked: int):
        """Envia notificaçao de inicio"""
        message = f"**Modo:** {mode}\n**Usernames ja verificados:** {total_checked}"
        return self.send_notification("🫆 Script Iniciado", message, 3447003)


class UsernameCache:
    """Cache pra usernames ja verificado"""

    def __init__(self, cache_file: str = "checked_users.json"):
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self) -> Dict:
        """Carrega cache do arquivo"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{Fore.YELLOW}Aviso: Não foi possível carregar cache: {e}")
        return {}

    def save_cache(self):
        """Salva cache"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Fore.RED}Erro ao salvar cache: {e}")

    def is_checked(self, username: str) -> bool:
        """Verifica se username já foi checado"""
        return username.lower() in self.cache

    def add_result(self, username: str, result: Dict):
        """Adiciona resultado ao cache"""
        self.cache[username.lower()] = {
            'disponivel': result.get('disponivel'),
            'timestamp': datetime.now().isoformat(),
            'detalhes': result.get('detalhes', ''),
            'metodo': result.get('metodo', '')
        }

    def get_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        total = len(self.cache)
        disponiveis = sum(1 for r in self.cache.values() if r.get('disponivel') is True)
        ocupados = sum(1 for r in self.cache.values() if r.get('disponivel') is False)
        erros = total - disponiveis - ocupados

        return {
            'total': total,
            'disponiveis': disponiveis,
            'ocupados': ocupados,
            'erros': erros
        }


class ScraperAPIManager:
    """Gerenciador de chaves ScraperAPI"""

    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys if api_keys else []
        self.current_key_index = 0
        self.invalid_keys = set()
        self.key_usage_count = {key: 0 for key in self.api_keys}
        self.key_errors = {key: 0 for key in self.api_keys}  

    def get_current_key(self) -> Optional[str]:
        """Retorna chave atual valida"""
        if not self.api_keys:
            return None

        valid_keys = [key for key in self.api_keys if key not in self.invalid_keys]
        if not valid_keys:
            print(f"{Fore.RED}Aviso: Chaves ScraperAPI Invalidas!")
            return None

        if self.current_key_index >= len(valid_keys):
            self.current_key_index = 0

        current_key = valid_keys[self.current_key_index]
        self.key_usage_count[current_key] += 1
        return current_key

    def rotate_key(self, failed_key: str, error_code: int = None) -> str:
        """Proxima chave pos falha"""
        self.key_errors[failed_key] += 1

        if error_code in [401, 403]:
            print(f"{Fore.YELLOW}Erro chave API! {error_code}: {failed_key[:10]}...")  
            self.invalid_keys.add(failed_key)

        valid_keys = [key for key in self.api_keys if key not in self.invalid_keys]
        if not valid_keys:
            print(f"{Fore.YELLOW}Todas as chaves ScraperAPI foram marcadas como inválidas!")
            return None

        self.current_key_index = (self.current_key_index + 1) % len(valid_keys)
        new_key = valid_keys[self.current_key_index]

        print(f"{Fore.CYAN}Rotacionando para nova chave ScraperAPI: {new_key[:10]}...")
        return new_key

    def get_stats(self) -> Dict:
        """Retorna estatisticas das chaves"""
        valid_keys = len([key for key in self.api_keys if key not in self.invalid_keys])  
        return {
            'total_keys': len(self.api_keys),
            'valid_keys': valid_keys,
            'invalid_keys': len(self.invalid_keys),
            'current_key_usage': self.key_usage_count,
            'key_errors': self.key_errors
        }


# Verificaçao dos Usernames pro discord ! (Parte principal) !!!
class DiscordUsernameVerifier:
    def __init__(self, proxies: List[str] = None, scraper_api_keys: List[str] = None, webhook_url: str = None):  
        self.endpoint = "https://discord.com/api/v9"
        self.headers = {"Content-Type": "application/json"}
        self.session = requests.Session()  

        self.proxies = proxies if proxies else []
        self.proxy_cycle = self._create_proxy_cycle() if self.proxies else None  

        if scraper_api_keys:
            self.scraper_manager = ScraperAPIManager(scraper_api_keys)
        else:
            env_key = os.getenv('SCRAPER_API_KEY')
            if env_key:
                self.scraper_manager = ScraperAPIManager([env_key])
            else:
                self.scraper_manager = ScraperAPIManager([])  

        self.cache = UsernameCache()
        self.webhook = WebhookManager(webhook_url)

        self.timeout = 30
        self.use_scraper_api = len(self.scraper_manager.api_keys) > 0

        self.stats = {
            'total_testados': 0,
            'disponiveis': 0,
            'ocupados': 0,
            'erros': 0,
            'rate_limits': 0,
            'key_rotations': 0,
            'tempo_inicio': None,  
            'usernames_pulados': 0
        }

        self.cache_resultados = {}
        self.usernames_encontrados = []
        self.running = False

    def _create_proxy_cycle(self):
        return itertools.cycle(self.proxies)

    def _get_proxy_dict(self, proxy_string: str) -> Dict:
        if '@' in proxy_string:
            auth, hostport = proxy_string.split('@')
            username, password = auth.split(':')
            host, port = hostport.split(':')
            return {
                "http": f"http://{username}:{password}@{host}:{port}",
                "https": f"http://{username}:{password}@{host}:{port}"
            }
        else:
            return {
                "http": f"http://{proxy_string}",
                "https": f"https://{proxy_string}"
            }

    def verificar_username_oficial(self, username: str, use_proxies: bool = True) -> Dict:
        if self.cache.is_checked(username):
            self.stats['usernames_pulados'] += 1
            cached_result = self.cache.cache[username.lower()]
            return {
                "username": username,
                "disponivel": cached_result.get('disponivel'),
                "detalhes": f"CACHED: {cached_result.get('detalhes', '')}",
                "tempo": 0,
                "metodo": f"CACHE_{cached_result.get('metodo', '')}",
                "status_code": None,
                "proxy_usado": "Cache",
                "scraper_key_used": None
            }

        resultado = {
            "username": username,
            "disponivel": None,
            "detalhes": "",
            "tempo": 0,
            "metodo": "ENDPOINT_OFICIAL",
            "status_code": None,
            "proxy_usado": None,
            "scraper_key_used": None
        }

        inicio = time.time()

        try:
            if self.use_scraper_api and use_proxies:
                if not self.scraper_manager.api_keys:
                    print(f"{Fore.RED}Nenhuma chave ScraperAPI encontrada. Encerrando script...")
                    self.running = False
                    raise SystemExit("Nenhuma chave ScraperAPI encontrada")
                resultado = self._verificar_com_scraper_api(username, resultado)

            elif use_proxies and self.proxies and self.proxy_cycle:
                proxy_string = next(self.proxy_cycle)
                proxy_dict = self._get_proxy_dict(proxy_string)
                resultado["proxy_usado"] = proxy_string
                response = self._request_with_proxy(username, proxy_dict)
                resultado["metodo"] += "_PROXY"
                self._processar_resposta(response, resultado)

            else:
                resultado["proxy_usado"] = "Direct"
                response = self._request_direct(username)
                resultado["metodo"] += "_DIRECT"
                self._processar_resposta(response, resultado)

        except requests.exceptions.RequestException as e:
            resultado["detalhes"] = f"ERRO CONEXÃO: {str(e)}"
            self.stats['erros'] += 1

        except Exception as e:
            resultado["detalhes"] = f"ERRO: {str(e)}"
            self.stats['erros'] += 1

        resultado["tempo"] = time.time() - inicio

        if resultado["disponivel"] is not None:
            self.cache.add_result(username, resultado)

            if resultado["disponivel"] and self.webhook.enabled:
                self.webhook.send_available_username(username, resultado["detalhes"])

        return resultado

    def _verificar_com_scraper_api(self, username: str, resultado: Dict) -> Dict:
        """Verifica username usando ScraperAPI com rotação automática de chaves"""
        max_tentativas = len(self.scraper_manager.api_keys)
        tentativas = 0

        while tentativas < max_tentativas:
            current_key = self.scraper_manager.get_current_key()
            if not current_key:
                print(f"{Fore.RED}Todas as chaves ScraperAPI foram esgotadas. Encerrando script...")
                resultado["detalhes"] = "SCRIPT ENCERRADO: Todas as chaves ScraperAPI esgotadas"
                self.running = False
                raise SystemExit("Todas as chaves ScraperAPI foram esgotadas")

            resultado["proxy_usado"] = "ScraperAPI"
            resultado["scraper_key_used"] = current_key[:10] + "..."
            resultado["metodo"] += "_SCRAPERAPI"

            try:
                response = self._request_with_scraper_api(username, current_key)

                if response.status_code in [401, 403]:
                    print(f"{Fore.YELLOW}Chave ScraperAPI com erro {response.status_code}, rotacionando...")
                    self.scraper_manager.rotate_key(current_key, response.status_code)
                    self.stats['key_rotations'] += 1
                    tentativas += 1
                    continue

                self._processar_resposta(response, resultado)
                break

            except requests.exceptions.RequestException as e:
                print(f"{Fore.YELLOW}Erro na chave {current_key[:10]}..., tentando próxima")
                self.scraper_manager.rotate_key(current_key)
                tentativas += 1
                if tentativas >= max_tentativas:
                    print(f"{Fore.RED}Todas as chaves ScraperAPI falharam. Encerrando script...")
                    resultado["detalhes"] = "SCRIPT ENCERRADO: Todas as chaves falharam"
                    self.running = False
                    raise SystemExit("Todas as chaves ScraperAPI falharam")
                continue

        return resultado

    def _processar_resposta(self, response: requests.Response, resultado: Dict):
        """Processa resposta HTTP e atualiza resultado"""
        resultado["status_code"] = response.status_code
        self.stats['total_testados'] += 1

        if response.status_code in [200, 201, 204]:
            response_data = response.json()

            if not response_data or response_data == {}:
                resultado["detalhes"] = "Resposta vazia da API"
                self.stats['erros'] += 1

            elif response_data.get("taken") is True:
                resultado["disponivel"] = False
                resultado["detalhes"] = "USERNAME OCUPADO"
                self.stats['ocupados'] += 1

            elif response_data.get("taken") is False:
                resultado["disponivel"] = True
                resultado["detalhes"] = "USERNAME DISPONÍVEL"
                self.stats['disponiveis'] += 1
                self.usernames_encontrados.append(resultado["username"])

            else:
                resultado["detalhes"] = f"Resposta inesperada: {response_data}"
                self.stats['erros'] += 1

        elif response.status_code == 429:
            self.stats['rate_limits'] += 1
            retry_after = response.json().get("retry_after", 60) if response.text else 60
            resultado["detalhes"] = f"RATE LIMITED - aguardar {retry_after}s"

            if not self.use_scraper_api:
                print(f"Rate limit - aguardando {retry_after}s...")
                time.sleep(retry_after)

        else:
            resultado["detalhes"] = f"ERRO HTTP {response.status_code}"
            self.stats['erros'] += 1

    def _request_with_scraper_api(self, username: str, api_key: str) -> requests.Response:
        scraper_url = f"http://api.scraperapi.com"
        params = {
            'api_key': api_key,
            'url': f'{self.endpoint}/unique-username/username-attempt-unauthed',
            'render': 'false',
            'premium': 'true'
        }

        return requests.post(
            scraper_url,
            params=params,
            headers=self.headers,
            json={"username": username},
            timeout=self.timeout
        )

    def _request_with_proxy(self, username: str, proxy_dict: Dict) -> requests.Response:
        return self.session.post(
            url=f"{self.endpoint}/unique-username/username-attempt-unauthed",
            headers=self.headers,
            json={"username": username},
            proxies=proxy_dict,
            timeout=self.timeout
        )

    def _request_direct(self, username: str) -> requests.Response:
        return self.session.post(
            url=f"{self.endpoint}/unique-username/username-attempt-unauthed",
            headers=self.headers,
            json={"username": username},
            timeout=self.timeout
        )

    def gerar_username_4_chars(self, tipo: str) -> str:
        if tipo == 'letters':
            chars = string.ascii_lowercase
            return ''.join(random.choices(chars, k=4))

        elif tipo == 'mixed':
            chars = string.ascii_lowercase + string.digits + '._'
            return ''.join(random.choices(chars, k=4))

        elif tipo == 'patterns':
            patterns = [
                lambda: random.choice(string.digits) + random.choice(string.ascii_lowercase) * 3,
                lambda: random.choice(string.digits) * 2 + random.choice(string.ascii_lowercase) + random.choice(
                    string.digits),
                lambda: random.choice(string.digits) * 3 + random.choice(string.ascii_lowercase),
                lambda: random.choice(string.digits) + random.choice(string.ascii_lowercase) + random.choice(
                    string.digits) + random.choice(string.ascii_lowercase)
            ]
            return random.choice(patterns)()

        elif tipo == 'special_patterns':
            patterns = [
                lambda: '__' + random.choice(string.digits),
                lambda: '__' + random.choice(string.ascii_lowercase) + '_',
                lambda: '_' + random.choice('.') + '_' + random.choice(string.ascii_lowercase),
                lambda: '_' + random.choice(string.digits) + '_' + random.choice(string.digits)
            ]
            return random.choice(patterns)()

        elif tipo == 'numbers':
            return ''.join(random.choices(string.digits, k=4))

        return 'erro'

    def gerar_username_5_numeros(self, tipo: str) -> str:
        """Gera usernames de 5 números puros ou mistos com pontos"""
        if tipo == 'pure':
            return ''.join(random.choices(string.digits, k=5))

        elif tipo == 'mixed':
            patterns = [
                lambda: f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                lambda: f"{random.randint(10, 99)}.{random.randint(0, 9)}",
                lambda: f"{random.randint(1, 9)}.{random.randint(10, 99)}"
            ]
            return random.choice(patterns)()

        return 'erro'

    def gerar_username_3_chars(self, tipo: str) -> str:
        if tipo == 'letters':
            chars = string.ascii_lowercase
            return ''.join(random.choices(chars, k=3))

        elif tipo == 'mixed':
            chars = string.ascii_lowercase + string.digits + '._'
            return ''.join(random.choices(chars, k=3))

        elif tipo == 'special':
            patterns = [
                lambda: random.choice(string.digits) + random.choice(string.ascii_lowercase) * 2,
                lambda: random.choice(string.ascii_lowercase) + random.choice(string.digits) + random.choice(
                    string.ascii_lowercase),
                lambda: random.choice(string.ascii_lowercase) * 2 + random.choice(string.digits),
                lambda: random.choice(string.digits) * 2 + random.choice(string.ascii_lowercase)
            ]
            return random.choice(patterns)()

        return 'erro'

    def gerar_padroes_customizados(self) -> str:
        """Gera usernames dos padrões customizados: .6uy, .uy3, _8s9, _9.8, _.s."""
        patterns = [
            lambda: f".{random.choice(string.digits)}{random.choice(string.ascii_lowercase)}{random.choice(string.ascii_lowercase)}",
            lambda: f".{random.choice(string.ascii_lowercase)}{random.choice(string.ascii_lowercase)}{random.choice(string.digits)}",
            lambda: f"_{random.choice(string.digits)}{random.choice(string.ascii_lowercase)}{random.choice(string.digits)}",
            lambda: f"_{random.choice(string.digits)}.{random.choice(string.digits)}",
            lambda: f"_.{random.choice(string.ascii_lowercase)}."
        ]

        return random.choice(patterns)()

    def executar_verificacao_continua(self, tipos_escolhidos: List[str], delay_min: float, delay_max: float,
                                      limite: Optional[int] = None):
        self.running = True
        self.stats['tempo_inicio'] = datetime.now()
        tentativas = 0

        try:
            while self.running:
                if limite and tentativas >= limite:
                    print(f"{Fore.GREEN}Limite de {limite} tentativas atingido!")
                    break

                if '9' in tipos_escolhidos:
                    tipo_escolhido = random.choice(['1', '2', '3', '4', '5', '6', '7', '8', '10', '11', '12'])
                else:
                    tipo_escolhido = random.choice(tipos_escolhidos)

                if tipo_escolhido == '1':
                    username = self.gerar_username_3_chars('letters')
                elif tipo_escolhido == '2':
                    username = self.gerar_username_3_chars('mixed')
                elif tipo_escolhido == '3':
                    username = self.gerar_username_4_chars('letters')
                elif tipo_escolhido == '4':
                    username = self.gerar_username_4_chars('mixed')
                elif tipo_escolhido == '5':
                    username = self.gerar_username_3_chars('special')
                elif tipo_escolhido == '6':
                    username = self.gerar_username_4_chars('patterns')
                elif tipo_escolhido == '7':
                    username = self.gerar_username_4_chars('special_patterns')
                elif tipo_escolhido == '8':
                    username = self.gerar_username_4_chars('numbers')
                elif tipo_escolhido == '10':
                    username = self.gerar_username_5_numeros('pure')
                elif tipo_escolhido == '11':
                    username = self.gerar_username_5_numeros('mixed')
                elif tipo_escolhido == '12':
                    username = self.gerar_padroes_customizados()
                else:
                    continue

                tentativas += 1

                resultado = self.verificar_username_oficial(username)

                if resultado["disponivel"] is True:
                    print(f"{Fore.GREEN}[{tentativas}] DISPONÍVEL: {username} - {resultado['detalhes']}")
                elif resultado["disponivel"] is False:
                    print(f"{Fore.RED}[{tentativas}] OCUPADO: {username}")
                else:
                    print(f"{Fore.YELLOW}[{tentativas}] ERRO: {username} - {resultado['detalhes']}")

                if tentativas % 50 == 0:
                    cache_stats = self.cache.get_stats()
                    tempo_decorrido = datetime.now() - self.stats['tempo_inicio']
                    print(
                        f"\n{Fore.CYAN}📊 Stats: {cache_stats['disponiveis']} disponíveis, {cache_stats['ocupados']} ocupados, {cache_stats['erros']} erros")
                    print(f"⏱️ Tempo: {tempo_decorrido}, 🎯 Tentativas: {tentativas}")

                delay = random.uniform(delay_min, delay_max)
                time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️ Script interrompido pelo usuário!")

        finally:
            self.cache.save_cache()
            self._mostrar_estatisticas_finais(tentativas)

    def _mostrar_estatisticas_finais(self, tentativas_totais: int):
        cache_stats = self.cache.get_stats()
        tempo_total = datetime.now() - self.stats['tempo_inicio']

        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.GREEN}🏁 VERIFICAÇÃO CONCLUÍDA!")
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"⏱Tempo total: {tempo_total}")
        print(f"Tentativas nesta sessão: {tentativas_totais}")
        print(f"Cache total: {cache_stats['total']} usernames")
        print(f"Disponíveis: {Fore.GREEN}{cache_stats['disponiveis']}")
        print(f"Ocupados: {Fore.RED}{cache_stats['ocupados']}")
        print(f"Erros: {Fore.YELLOW}{cache_stats['erros']}")

        if self.usernames_encontrados:
            print(f"\n{Fore.GREEN}🎉 USERNAMES DISPONÍVEIS ENCONTRADOS:")
            for username in self.usernames_encontrados[-10:]:
                print(f"    {username}")


def carregar_keys_do_arquivo():
    proxies = []
    scraper_keys = []

    base_dir = os.path.dirname(os.path.abspath(__file__))

    key_path = os.path.join(base_dir, "key.txt")

    try:
        if os.path.exists(key_path):

            with open(key_path, "r", encoding="utf-8") as f:
                for linha in f:

                    linha = linha.strip()

                    if not linha or linha.startswith("#"):
                        continue

                    # chave scraperapi (32 caracteres hex)
                    if len(linha) == 32 and all(c in "0123456789abcdefABCDEF" for c in linha):
                        scraper_keys.append(linha)

                    # proxy
                    elif ":" in linha:
                        proxies.append(linha)

        else:
            print(f"{Fore.YELLOW}Arquivo key.txt não encontrado em: {key_path}")
    except Exception as e:
        print(f"{Fore.RED}Erro ao carregar key.txt: {e}")
    return proxies, scraper_keys


def carregar_configuracao():
    """Carrega configuração básica e keys do arquivo"""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    config_padrao = {
        "proxies": [],
        "scraper_api_keys": [],
        "webhook_url": "",
        "delay_min": 1.3,
        "delay_max": 1.3
    }

    proxies, scraper_keys = carregar_keys_do_arquivo()
    config_padrao["proxies"] = proxies
    config_padrao["scraper_api_keys"] = scraper_keys

    config_path = os.path.join(base_dir, "config.json")

    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "delay_min" in config:
                    config_padrao["delay_min"] = config["delay_min"]
                if "delay_max" in config:
                    config_padrao["delay_max"] = config["delay_max"]
    except Exception as e:
        print(f"{Fore.YELLOW}Erro ao carregar config.json: {e}")

    return config_padrao


def main():
    mostrar_banner()

    config = carregar_configuracao()

    webhook_url = input(f"\n{Fore.RED}Discord Webhook : ").strip()

    os.system('cls' if os.name == 'nt' else 'clear')
    mostrar_banner()

    verificador = DiscordUsernameVerifier(
        proxies=config.get("proxies", []),
        scraper_api_keys=config.get("scraper_api_keys", []),
        webhook_url=webhook_url
    )

    while True:
        print(f"\n{Fore.RED}=== MENU PRINCIPAL ===")
        print("1. 3 letras puras (exemplo: abc, def)")
        print("2. 3 letras mistas (exemplo: 7h8, p.3, ci_)")
        print("3. 4 letras puras (exemplo: abcd, efgh)")
        print("4. 4 letras mistas (exemplo: a98s, h3k9)")
        print("5. Especiais 3 chars (exemplo: 6_r, 4j_, 8q.)")
        print("6. Padrões 4 letras (exemplo: 2bbb, 33c3, 555w, 8p8p)")
        print("7. Padrões especiais (exemplo: __.4, __w_, _._c, _6_6)")
        print("8. 4 números (exemplo: 3393, 8092)")
        print("10. 5 números puros (exemplo: 53878, 17283) [NOVO]")
        print("11. 5 números mistos (exemplo: 5.3.4, 1.2.4, 8.2.2) [NOVO]")
        print("12. Padrões customizados (.6uy, .uy3, _8s9, _9.8, _.s.) [NOVO]")
        print("9. Todos os tipos misturados")
        print("0. Sair")

        opcao = input(f"\n{Fore.RED}Escolha uma ou múltiplas opções (ex: 3,4,5): ").strip()

        if opcao == "0":
            print(f"{Fore.GREEN}Obrigado por usar o Discord Username Checker!")
            break

        opcoes_validas = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        opcoes_escolhidas = []

        if ',' in opcao:
            for op in opcao.split(','):
                op = op.strip()
                if op in opcoes_validas:
                    opcoes_escolhidas.append(op)
        else:
            if opcao in opcoes_validas:
                opcoes_escolhidas.append(opcao)

        if opcoes_escolhidas:
            try:
                limite = input(f"{Fore.CYAN}Limite de tentativas (Enter para infinito): ").strip()
                limite_int = int(limite) if limite else None

                delay_input = input(f"{Fore.CYAN}Delay entre verificações em segundos (padrão 1.3): ").strip()
                if delay_input:
                    if '-' in delay_input:
                        delay_min, delay_max = map(float, delay_input.split('-'))
                    else:
                        delay_min = delay_max = float(delay_input)
                else:
                    delay_min, delay_max = config.get("delay_min", 1.3), config.get("delay_max", 1.3)

                tipos_nomes = {
                    "1": "3 letras puras",
                    "2": "3 letras mistas",
                    "3": "4 letras puras",
                    "4": "4 letras mistas",
                    "5": "Especiais 3 chars",
                    "6": "Padrões 4 letras",
                    "7": "Padrões especiais",
                    "8": "4 números",
                    "9": "Todos misturados",
                    "10": "5 números puros",
                    "11": "5 números mistos",
                    "12": "Padrões customizados (.6uy, .uy3, _8s9, _9.8, _.s.)"
                }

                os.system('cls' if os.name == 'nt' else 'clear')
                mostrar_banner()

                if len(opcoes_escolhidas) > 1:
                    tipos_str = ", ".join([tipos_nomes[op] for op in opcoes_escolhidas])
                    print(f"{Fore.CYAN}Tipos selecionados: {tipos_str}")
                else:
                    print(f"{Fore.GREEN}Iniciando verificação: {tipos_nomes.get(opcoes_escolhidas[0], 'Desconhecido')}")

                verificador.executar_verificacao_continua(opcoes_escolhidas, delay_min, delay_max, limite_int)

            except ValueError:
                print(f"{Fore.RED}Valor inválido inserido!")
            except Exception as e:
                print(f"{Fore.RED}Erro: {e}")
        else:
            print(f"{Fore.RED}Opção inválida!")


if __name__ == "__main__":
    main()