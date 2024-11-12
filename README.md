
# Automação de Bases Controladoria

Este projeto tem como objetivo automatizar o processo de download, extração e organização de bases de dados públicas, como Siconv, Portal de Convênios, e Orçamento Geral da União, utilizando Selenium e Python.

## Estrutura do Projeto

```plaintext
AUTOMACAO_BASES_CONTROLADORIA/
├── download/
│   ├── __init__.py
│   ├── BaseDownloader.py
│   ├── OrcamentoDownloader.py
│   ├── PortalConvenioDownloader.py
│   ├── SiconvDownloader.py
├── venv/
├── LICENSE
├── main.py
├── README.md
```

### Diretórios e Arquivos

- **`download/`**: Contém os módulos responsáveis por realizar o download e o processamento dos arquivos.
  - **`BaseDownloader.py`**: Classe base que define a interface para downloaders.
  - **`OrcamentoDownloader.py`**: Classe específica para o download e extração de dados do Orçamento Geral da União.
  - **`PortalConvenioDownloader.py`**: Classe para download e extração de dados do Portal de Convênios.
  - **`SiconvDownloader.py`**: Classe para download e extração de dados do Siconv.
- **`main.py`**: Arquivo principal para executar as funções de download e processamento.
- **`LICENSE`**: Informações de licenciamento do projeto.
- **`README.md`**: Documentação do projeto.

## Pré-requisitos

Certifique-se de ter os seguintes softwares instalados:

- Python 3.8 ou superior
- Pip (Gerenciador de pacotes do Python)
- Navegador Firefox
- Geckodriver (gerenciado automaticamente pelo Webdriver Manager)

## Instalação

1. Clone este repositório:

   ```bash
   git clone https://github.com/Alyssandro1771415/automacao_bases_controladoria.git
   cd automacao_bases_controladoria
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

## Uso

Para realizar o download e extração de uma das bases, edite o arquivo `main.py` para chamar o respectivo downloader e execute:

```bash
python main.py
```

### Exemplo de uso no `main.py`

```python
from download.OrcamentoDownloader import OrcamentoDownloader

orcamento_downloader = OrcamentoDownloader("caminho/para/diretorio_de_download", "caminho_para_diretorio_de_destino_final")
orcamento_downloader.download()
```

## Funcionalidades

- **Setup Automático de Diretórios**: Verifica e cria os diretórios necessários automaticamente.
- **Download Automático**: Realiza downloads de arquivos zipados diretamente das fontes oficiais.
- **Extração e Organização**: Extrai os arquivos, organiza-os e remove os arquivos zip temporários.
- **Renomeação Automática**: Suporte para renomeação de arquivos conforme padrões estabelecidos.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir um *issue* ou enviar um *pull request* que permitam o projeto ser mais robusto e amplo.

## Licença

Este projeto está licenciado sob os termos da licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
