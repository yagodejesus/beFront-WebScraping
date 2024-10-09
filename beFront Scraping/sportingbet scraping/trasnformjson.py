from flask import Flask, render_template, request, send_file, redirect, url_for
import json
import os

app = Flask(__name__)

# Diretório onde os arquivos JSON serão salvos
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Certifique-se de que o diretório de upload existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Rota para exibir o formulário e colar o conteúdo do JSON
@app.route('/', methods=['GET', 'POST'])
def index():
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

            # Redireciona para o download do arquivo JSON salvo
            return redirect(url_for('download_json', filename='arquivo.json'))

        except ValueError as e:
            return f"Erro ao processar o JSON: {e}"

    return render_template('trasnformjson.html')

if __name__ == '__main__':
    app.run(debug=True)