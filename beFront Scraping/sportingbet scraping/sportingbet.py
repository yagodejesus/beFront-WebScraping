from flask import Flask, render_template, request, make_response
import json
import pandas as pd
import re
import io
import os

app = Flask(__name__)

# Configurar pasta de uploads
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Certifique-se de que o diretório de upload existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Variável global para armazenar o DataFrame processado
df_global = pd.DataFrame()

# Função para limpar os dados
def clean_text(text):
    if isinstance(text, str):
        # Remove \n, \r, \t e múltiplos espaços
        text = re.sub(r'[\n\r\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    return text

# Função para limpar todo o conteúdo do JSON
def clean_data(obj):
    if isinstance(obj, str):
        return clean_text(obj)
    elif isinstance(obj, list):
        return [clean_data(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: clean_data(value) for key, value in obj.items()}
    return obj

# Função para carregar e processar os dados do JSON enviado pelo usuário
def load_data(json_file_path):
    try:
        with open(json_file_path, encoding='utf-8') as f:
            data = json.load(f)
            data = clean_data(data)
    except Exception as e:
        print(f"Erro ao carregar o arquivo JSON: {e}")
        return pd.DataFrame()

    df_result = pd.DataFrame()

    try:
        for fixture in data['fixtures']:
            if fixture.get('optionMarkets'):
                options = fixture['optionMarkets'][0].get('options', [])
                options_names = [clean_text(option.get('name', {}).get('value', '')) for option in options]
                options_sources = [clean_text(option.get('sourceName', {}).get('value', '')) for option in options]
                options_odds = [clean_text(str(option.get('price', {}).get('odds', 'N/A'))) for option in options]
                options_game = clean_text(fixture.get('sourceId', 'N/A'))
                options_date = clean_text(fixture.get('startDate', 'N/A'))
                options_type_sport = clean_text(fixture.get('sport', {}).get('name', {}).get('value', 'N/A'))
                options_league = clean_text(fixture.get('competition', {}).get('name', {}).get('value', 'N/A'))
                options_status_participante = ['HomeTeam', 'draw', 'AwayTeam']

                df = pd.DataFrame({
                    'name': options_names,
                    'sourceName': options_sources,
                    'odds': options_odds,
                    'game_id': options_game,
                    'game_date': options_date,
                    'sport_type': options_type_sport,
                    'sport_league': options_league,
                    'status_participant': options_status_participante
                })

                df_result = pd.concat([df_result, df], ignore_index=True)
    except Exception as e:
        print(f"Erro ao processar os dados: {e}")
        return pd.DataFrame()

    return df_result

# Rota principal para o upload do arquivo e exibição da tabela
@app.route('/', methods=['GET', 'POST'])
def index():
    global df_global  # Usar a variável global
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Nenhum arquivo foi enviado."
        
        file = request.files['file']
        if file.filename == '':
            return "Nenhum arquivo selecionado."

        if file and file.filename.endswith('.json'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            df_global = load_data(file_path)
            if df_global.empty:
                return "Nenhum dado foi encontrado ou houve um erro ao processar os dados."
            
            table_html = df_global.to_html(classes='data', header="true", index=False).replace('\n', '')
            return render_template('sportingbetTemplate.html', tables=table_html)
    
    return render_template('upload.html')

# Rota para baixar o CSV
@app.route('/download_csv')
def download_csv():
    global df_global  # Usar a variável global
    if df_global.empty:
        return "Nenhum dado foi encontrado ou houve um erro ao processar os dados."

    # Gerar CSV em memória
    output = io.StringIO()
    df_global.to_csv(output, index=False)
    output.seek(0)

    # Preparar a resposta para download
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=sportingbet_data.csv"
    response.headers["Content-type"] = "text/csv"
    return response

if __name__ == '__main__':
    app.run(debug=True)


