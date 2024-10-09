from flask import Flask, render_template, make_response, request, jsonify
import csv
import requests

app = Flask(__name__)

# URLs das APIs
url1 = 'https://events-api.apostaganha.bet/v5/events?idTournament=16478&onlyLiveEvents=false&onlyWinnersMarket=true'
url2 = 'https://events-api.apostaganha.bet/v5/events?idTournament=16493&onlyLiveEvents=false&onlyWinnersMarket=true'
url3 = 'https://events-api.apostaganha.bet/v5/events?idTournament=16724&onlyLiveEvents=false&onlyWinnersMarket=true'

def get_combined_data():
    response1 = requests.get(url1)
    response2 = requests.get(url2)
    response3 = requests.get(url3)

    if response1.status_code == 200 and response2.status_code == 200 and response3.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()
        combined_data = data1 + data2 + data3
        return combined_data
    else:
        return None

# Função para buscar detalhes do evento por srIdEvent e filtrar os mercados "Acima/Abaixo" e "Handicap Asiático"
def get_event_details_filtered(sr_id_event):
    details_url = f"https://events-api.apostaganha.bet/v5/events/detail/{sr_id_event}"
    response = requests.get(details_url)
    
    if response.status_code == 200:
        event_data = response.json()
        filtered_data = {"markets": []}
        
        # Percorrer os grupos e mercados para filtrar "Acima/Abaixo" e "Handicap Asiático"
        for group in event_data.get("groups", []):
            for market in group.get("marketList", []):
                if "Acima/Abaixo" in market.get("name"):
                    filtered_data["markets"].append(market)
        
        # Verificar se existe o campo customMarketList
        for custom_market in event_data.get("groups", []):
            for custom_market_list in custom_market.get("customMarketList", []):
                if "Handicap Asiático" in custom_market_list.get("name"):
                    filtered_data["markets"].append(custom_market_list)

        return filtered_data
    else:
        return None

@app.route('/')
def index():
    events = get_combined_data()
    
    # Inicializando event_data como None
    event_data = None
    
    if events is not None:
        return render_template('index.html', events=events, event_data=event_data)
    else:
        return "Erro ao acessar as APIs."


@app.route('/search_event', methods=['POST'])
def search_event():
    sr_id_event = request.form.get('srIdEvent')
    event_data = get_event_details_filtered(sr_id_event)
    
    events = get_combined_data()  # Mantendo os eventos principais

    if event_data:
        return render_template('index.html', events=events, event_data=event_data, sr_id_event=sr_id_event)
    else:
        return render_template('index.html', events=events, event_data=None, error="Nenhum dado encontrado para o srIdEvent fornecido.")


# Rota para baixar CSV dos eventos principais
@app.route('/download_csv')
def download_csv():
    events = get_combined_data()

    if events is not None:
        output = []
        output.append(['ID Evento', 'SR ID Evento', 'Data', 'Slug', 'Times', 'Mercados', 'Esporte', 'Torneio', 'Pontuação ao Vivo'])

        for event in events:
            times = ', '.join([f"{team['name']} ({'Casa' if team['isHome'] else 'Visitante'})" for team in event.get('teams', [])])
            mercados = ', '.join([market['name'] for market in event.get('marketList', [])])
            esporte = event.get('sport', {}).get('name', 'N/A')
            torneio = event.get('tournament', {}).get('name', 'N/A')
            score = f"Casa: {event.get('liveScore', {}).get('homeScore', 'N/A')} - Visitante: {event.get('liveScore', {}).get('awayScore', 'N/A')}"

            sr_id_event = event.get('srIdEvent', 'N/A')
            id_event = event.get('idEvent', 'N/A')

            output.append([id_event, sr_id_event, event.get('date', 'N/A'), event.get('slug', 'N/A'), times, mercados, esporte, torneio, score])

        si = make_response("\n".join([",".join(map(str, row)) for row in output]))
        si.headers["Content-Disposition"] = "attachment; filename=events.csv"
        si.headers["Content-type"] = "text/csv"

        return si
    else:
        return "Erro ao acessar as APIs."


# Rota para baixar CSV dos detalhes filtrados do evento
@app.route('/download_filtered_csv', methods=['POST'])
def download_filtered_csv():
    sr_id_event = request.form.get('srIdEvent')
    event_data = get_event_details_filtered(sr_id_event)

    if event_data is not None:
        output = []
        output.append(['Mercado', 'Label', 'Odds'])

        # Adicionando dados de "Acima/Abaixo"
        for market in event_data["markets"]:
            if "Acima/Abaixo" in market["name"]:
                for outcome in market["outcomes"]:
                    output.append([market["name"], outcome["label"], outcome["odds"]])

        # Adicionando dados de "Handicap Asiático"
        for market in event_data["markets"]:
            if "Handicap Asiático" in market["name"]:
                for header in market["headers"]:
                    for outcome in header["outcomes"]:
                        output.append([market["name"], outcome["label"], outcome["odds"]])

        # Criar resposta CSV
        si = make_response("\n".join([",".join(map(str, row)) for row in output]))
        si.headers["Content-Disposition"] = f"attachment; filename=event_{sr_id_event}_details.csv"
        si.headers["Content-type"] = "text/csv"

        return si
    else:
        return "Erro ao acessar os detalhes do evento."


if __name__ == '__main__':
    app.run(debug=True)
