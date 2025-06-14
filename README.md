# Ferramenta de Varredura e Monitoramento de Rede

Este projeto é uma ferramenta de varredura e monitoramento de rede desenvolvida para a disciplina de Redes 2 da Pontifícia Universidade Católica de Goiás (PUC-Goiás). Ela permite a descoberta de rede, coleta de informações de hosts (IP, MAC, fabricante, nome DNS) e recuperação de dados SNMP (Simple Network Management Protocol) de dispositivos ativos.

## Funcionalidades

* **Descoberta de Hosts:**
    * **Varredura ARP:** Descobre hosts na rede local usando requisições ARP.
    * **Varredura Rápida com Ping:** Utiliza multi-threading para identificar rapidamente hosts ativos via ping ICMP.
    * **Varredura de Host Único:** Coleta informações para um endereço IP específico.
* **Coleta de Informações:**
    * Recupera endereços MAC e tenta identificar o fabricante.
    * Resolve nomes de hosts DNS.
    * Coleta informações SNMP (Descrição do Sistema, Tempo de Atividade, Uso de CPU, Memória, etc.) de dispositivos habilitados para SNMP.
* **Arquitetura Cliente-Servidor:**
    * Um servidor escuta por conexões de clientes e processa requisições de varredura de rede.
    * Lida com múltiplas conexões de clientes concorrentemente usando threads.
    * Fornece saída estruturada das informações dos hosts descobertos.

## Estrutura do Projeto

A estrutura do projeto é a seguinte:

```
network_scanner/
├── src/
│   ├── __init__.py
│   ├── host_scanner.py
│   ├── mac_vendor_lookup.py
│   ├── main.py
│   ├── network_scanner_server.py
│   └── snmp_helper.py
├── tests/
│   └── client.py
├── config_files/
│   └── snmpd.conf.example
├── venv/
├── README.md
└── requirements.txt
```

## Instruções de Configuração

Para começar com este projeto, siga estes passos:

### 1. Criar um Ambiente Virtual

É altamente recomendável usar um ambiente virtual para gerenciar as dependências do projeto e evitar conflitos com os pacotes Python do seu sistema.

```bash
python3 -m venv venv
```

### 2. Ativar o Ambiente Virtual

No Windows:

```bash
.\venv\Scripts\activate
```

No macOS/Linux:

```bash
source venv/bin/activate
```

### 3. Instalar as Dependências Python

Com seu ambiente virtual ativado, instale as bibliotecas Python necessárias usando pip:

```bash
pip install -r requirements.txt
```

Isso instalará `scapy`, `getmac`, `pysnmp` e `pysnmp-mibs`.

### 4. Instalar e Configurar o SNMP

Para que as funcionalidades SNMP desta ferramenta funcionem corretamente, você precisa ter os utilitários SNMP e MIBs instalados e, possivelmente, configurar o agente SNMP nos dispositivos que deseja monitorar.

#### Instalando Utilitários SNMP e MIBs

**Nota Importante:** O arquivo `snmp_helper.py` usa `pysnmp` diretamente, que lida com a resolução de MIBs programaticamente. No entanto, ter utilitários SNMP em todo o sistema (`snmpget`, `snmpwalk`, etc.) e MIBs pode ser útil para depuração e gerenciamento geral de rede.

**Fedora:**

```bash
sudo dnf install net-snmp net-snmp-utils
sudo dnf install net-snmp-libs net-snmp-perl net-snmp-python
# Para baixar MIBs adicionais (opcional, mas recomendado para funcionalidade completa)
sudo dnf install net-snmp-data
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install snmp snmpd snmp-mibs-downloader
# Para disponibilizar MIBs baixados em todo o sistema (editar /etc/snmp/snmp.conf)
sudo sed -i 's/^#mibs :/mibs :/' /etc/snmp/snmp.conf
```

**Windows:**

- **Baixar Net-SNMP:** Vá para o site oficial do Net-SNMP (http://www.net-snmp.org/download.html) e baixe a última versão estável para Windows.
- **Instalação:** Execute o instalador e siga as instruções na tela. Durante a instalação, certifique-se de selecionar para instalar as "Common tools" e "MIBs".
- **Variáveis de Ambiente (Opcional, mas Recomendado):** Adicione o diretório bin do Net-SNMP (ex: `C:\Program Files\Net-SNMP\bin`) à variável de ambiente PATH do seu sistema para executar facilmente `snmpget`, `snmpwalk`, etc., de qualquer prompt de comando.
- **MIBs:** O Net-SNMP no Windows geralmente instala os MIBs em um local como `C:\usr\share\snmp\mibs`.

#### Configurando o Agente SNMP (snmpd.conf)

Para permitir que outros dispositivos consultem informações SNMP de uma máquina Linux (ex: se você deseja escanear sua própria máquina Linux), você precisa configurar o daemon SNMP (`snmpd`).

**Usando o Arquivo de Configuração de Exemplo:**

Você pode encontrar um arquivo de configuração de exemplo pré-configurado para o `snmpd` no seu repositório, em `config_files/snmpd.conf.example`. Este arquivo já inclui as diretivas para CPU, memória e outros OIDs necessários para o funcionamento completo da ferramenta.

Para usá-lo, siga estes passos:

- Navegue até a raiz do seu projeto:

```bash
cd /caminho/para/seu/projeto/network_scanner
```

- Crie um backup do seu arquivo `snmpd.conf` original (altamente recomendado!):

```bash
sudo cp /etc/snmp/snmpd.conf /etc/snmp/snmpd.conf.bak
```

- Copie o arquivo de exemplo para o local correto do sistema:

```bash
sudo cp config_files/snmpd.conf.example /etc/snmp/snmpd.conf
```

- Edite o arquivo copiado para personalizar sua string de comunidade SNMP:
  Abra o arquivo `/etc/snmp/snmpd.conf` com um editor de texto (como nano):

```bash
sudo nano /etc/snmp/snmpd.conf
```

- Localize a linha `rocommunity your_community_string` e substitua `your_community_string` pela sua própria string de comunidade SNMP (ex: `rocommunity public`).

- Você também pode ajustar as linhas `com2sec` (comentadas por padrão no exemplo) para restringir quais IPs podem consultar seu agente SNMP, se desejar.

- Após qualquer modificação, salve o arquivo (Ctrl+O, Enter, Ctrl+X no nano).

**Reiniciar o Serviço SNMP:**

Após copiar e ajustar o arquivo de configuração, você deve reiniciar o serviço SNMP para que as alterações entrem em vigor:

```bash
sudo systemctl restart snmpd # Para sistemas baseados em systemd (Fedora, Ubuntu)
# sudo service snmpd restart # Para sistemas init mais antigos (se aplicável)
```

#### Configurando para Windows (Serviço SNMP):

No Windows, o SNMP é instalado como um "Recurso" e configurado através dos Serviços.

**Instalar Recurso SNMP:**

- Vá para Painel de Controle -> Programas e Recursos -> Ativar ou desativar recursos do Windows.
- Role para baixo e marque *Recurso SNMP* (e *Provedor WMI de SNMP* se disponível).
- Clique em OK e siga os prompts.

**Configurar Serviço SNMP:**

- Abra *Serviços* (procure por "Serviços" no Menu Iniciar).
- Encontre *Serviço SNMP* na lista, clique com o botão direito e vá em *Propriedades*.
- Vá para a aba *Segurança*.
- Em *Nomes de Comunidade Aceitos*, clique em *Adicionar...*.
- Selecione *Somente Leitura* para *Direitos da Comunidade*.
- Insira o *Nome da Comunidade* desejado (ex: `public`). Clique em *Adicionar*.
- Em *Aceitar pacotes SNMP destes hosts*, selecione *Adicionar...* para especificar os endereços IP permitidos (ex: o IP da máquina que executa seu scanner). Para testes, você pode selecionar *Aceitar pacotes SNMP de qualquer host*, mas isso não é recomendado para produção.
- Vá para a aba *Agente* e preencha as informações relevantes do sistema (*Contato*, *Localização*, *Serviços*).
- Clique em *Aplicar* e *OK*.
- Reinicie o *Serviço SNMP*.

### 5. Executando o Servidor

Certifique-se de que seu ambiente virtual esteja ativado. Em seguida, execute o script `main.py`:

```bash
python src/main.py
```

Você deverá ver a mensagem `Servidor escutando na porta 35640...`.

### 6. Como Usar o Cliente

Como você já possui o arquivo `client.py` no diretório `tests/`, você pode usá-lo para interagir com o servidor.

- Abra um novo terminal.
- Navegue até o diretório raiz do seu projeto.
- Execute o cliente:

```bash
python tests/client.py
```

O cliente irá pedir que você digite a rede no formato CIDR. Por exemplo:

- Para escanear uma rede completa: `192.168.1.0/24`
- Para escanear um único host: `192.168.1.10/32`

Pressione Enter e o cliente enviará a requisição ao servidor e exibirá os resultados.

## Notas Importantes

- **Permissões:** A varredura ARP e as operações de socket brutas (usadas pelo Scapy) frequentemente exigem privilégios elevados (ex: executar com `sudo` no Linux). Se você encontrar erros de permissão, tente executar seu `main.py` com `sudo`.
- **Firewall:** Certifique-se de que seu firewall não esteja bloqueando conexões de entrada na porta `35640` na máquina do servidor, e conexões de saída no cliente.
- **String de Comunidade SNMP:** A string de comunidade SNMP padrão usada em `snmp_helper.py` é `public`. Se seus dispositivos usarem uma string de comunidade diferente, você precisará modificar `snmp_helper.py` para refletir isso.
- **MIBs:** Embora `pysnmp` tente resolver MIBs, alguns OIDs específicos do fornecedor podem exigir que arquivos MIB adicionais sejam carregados corretamente por `pysnmp-mibs`.