import os
import subprocess
from flask import Flask, request, send_file, jsonify
from spleeter.separator import Separator
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configurações de extensão de arquivos permitidos
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API está funcionando!"})

@app.route("/process-audio", methods=["POST"])
def process_audio():
    """
    Endpoint para processar o áudio.
    Envia um arquivo com os parâmetros:
    - file: Arquivo de áudio (mp3/wav).
    - remove_part: Nome da faixa a ser removida (opcional, ex.: 'vocals').
    - stems: Número de stems para separação (opções: 2, 4, 5).
    """
    try:
        # Dados enviados pelo cliente
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
        if file and allowed_file(file.filename):
            # Salva o arquivo temporariamente no servidor
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Parâmetros adicionais
            remove_part = request.form.get("remove_part", None)
            stems = int(request.form.get("stems", 4))  # Padrão: 4 stems

            # Validações básicas
            if stems not in [2, 4, 5]:
                return jsonify({"error": "O parâmetro 'stems' deve ser 2, 4 ou 5"}), 400

            if remove_part and remove_part not in ["vocals", "bass", "drums", "other", "piano"]:
                return jsonify({"error": f"A faixa '{remove_part}' não é válida"}), 400

            # Garante que o diretório de saída existe
            output_dir = os.path.join(UPLOAD_FOLDER, "output")
            os.makedirs(output_dir, exist_ok=True)

            # Inicializa o separador com o número de stems configurado
            separator = Separator(f"spleeter:{stems}stems")

            # Realiza a separação do áudio
            separator.separate_to_file(file_path, output_dir)

            # Caminho do diretório onde os stems foram salvos
            processed_dir = os.path.join(output_dir, os.path.splitext(filename)[0])

            # Remover a faixa especificada
            if remove_part:
                part_path = os.path.join(processed_dir, f"{remove_part}.wav")
                if os.path.exists(part_path):
                    os.remove(part_path)

            # Reconstruir o áudio sem a faixa removida
            remaining_parts = [
                os.path.join(processed_dir, f"{stem}.wav") for stem in ["vocals", "bass", "drums", "other", "piano"]
                if os.path.exists(os.path.join(processed_dir, f"{stem}.wav")) and (remove_part != stem)
            ]

            # Crie um arquivo de áudio com as faixas restantes
            output_audio_path = os.path.join(output_dir, f"processed_{filename}")
            remaining_parts = [part for part in remaining_parts if part]  # Filtra faixas existentes

            # Se restarem faixas para recomposição
            if remaining_parts:
                # Montando o comando para usar o ffmpeg e mixar os arquivos restantes
                filter_complex = f"amix=inputs={len(remaining_parts)}:duration=longest"

                cmd = ['ffmpeg', '-y']

                #Adiciona entradas para todas as faixas restantes
                for i, part in enumerate(remaining_parts):
                    cmd.append('-i')
                    cmd.append(part)

                # Cria a parte do filter_complex com os índices corretos
                filter_complex = ''.join([f"[{i}]" for i in range(len(remaining_parts))]) + f"amix=inputs={len(remaining_parts)}:duration=longest"

                # Adiciona o filter_complex e o caminho de saída
                cmd.extend(['-filter_complex', filter_complex, output_audio_path])

                # Executa o comando ffmpeg
                subprocess.run(cmd, check=True)
                
                # Remove o arquivo temporário original após o processamento
                os.remove(file_path)

            # Envia o arquivo processado como download
            return send_file(output_audio_path, as_attachment=True, download_name=f"processed_{filename}", mimetype="audio/wav")

        else:
            return jsonify({"error": "Arquivo inválido. Envie um arquivo mp3 ou wav."}), 400

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Erro ao executar o comando subprocess: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
