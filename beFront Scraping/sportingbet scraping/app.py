from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import json
import pandas as pd
import io
from sportingbet import make_response, load_data

app = Flask(__name__)

# Definir o diretório de upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')


# Rota principal para servir a página inicial "home.html"
@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

# Rota para upload de arquivos JSON e exibição de tabela
@app.route('/sportingbet', methods=['GET', 'POST'])
def sportingbet():
    global df_global  # Usar a variável global
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Nenhum arquivo foi enviado."
        
        file = request.files['file']
        if file.filename == '':
            return "Nenhum arquivo selecionado."

        if file and file.filename.endswith('.json'):
            # Certificar-se de que a pasta de upload existe
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            # Salvar o arquivo no diretório de upload
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Carregar os dados do arquivo JSON
            df_global = pd.read_json(file_path)
            if df_global.empty:
                return "Nenhum dado foi encontrado ou houve um erro ao processar os dados."
            
            # Gerar a tabela HTML
            table_html = df_global.to_html(classes='data', header="true", index=False).replace('\n', '')
            return render_template('sportingbetTemplate.html', tables=table_html)
    
    return render_template('upload.html')

# Rota para exibir o formulário e colar o conteúdo do JSON
@app.route('/upload_json', methods=['GET', 'POST'])
def upload_json():
    if request.method == 'POST':
        # Obtém o conteúdo colado do formulário
        json_content = request.form.get('json_content')

        if not json_content:
            return "Nenhum conteúdo foi colado."

        # Nome do arquivo JSON que será salvo
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'arquivo.json')

        try:
            # Converte o texto colado em JSON e salva em um arquivo
            json_data = json.loads(json_content)
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)

            return redirect(url_for('download_json', filename='arquivo.json'))

        except ValueError as e:
            return f"Erro ao processar o JSON: {e}"

    return render_template('trasnformjson.html')

# Rota para baixar o arquivo JSON salvo
@app.route('/download_json/<filename>')
def download_json(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
