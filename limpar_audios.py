import os
import sys
import subprocess
import shutil

# Forçar output em utf-8 no Windows para nomes com acentos e unicode
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class AudioCleanerApp:
    def __init__(self):
        # Tudo fica isolado dentro do diretorio atual do script
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_dir = os.path.join(self.base_dir, "Colocar Audios Aqui")
        self.output_dir = os.path.join(self.base_dir, "Audios_Limpos")
        self.temp1 = os.path.join(self.base_dir, "temp1_tmp.wav")
        self.temp2 = os.path.join(self.base_dir, "temp2_tmp.wav")
        self._setup_directories()

    def _setup_directories(self):
        # Cria as pastas se não existirem
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _clean_temp_files(self):
        if os.path.exists(self.temp1): os.remove(self.temp1)
        if os.path.exists(self.temp2): os.remove(self.temp2)

    def run(self):
        print("\n=========================================================")
        print("   Limpador de Áudio PRO - Modos IA e Estúdio")
        print("=========================================================\n")
        
        arquivos = [f for f in os.listdir(self.input_dir) if f.lower().endswith(('.aac', '.mp3', '.wav', '.m4a'))]
        
        if not arquivos:
            print(f"Nenhum áudio encontrado.\nPor favor, copie seus áudios para a pasta:\n -> {self.input_dir}")
            print("E depois abra o script novamente!")
            return

        print("Escolha o fluxo de limpeza:")
        print(" [1] Inteligência Artificial Pura (DeepFilterNet)")
        print("     -> Máxima aniquilação de multidão/barulho de fundo.")
        print("     -> Recomendado para eventos caóticos (BGS, CCXP).")
        print(" [2] Tratamento de Podcaster (Algoritmo + Gate + Compressor)")
        print("     -> Redução leve de chiado com forte tratamento de rádio.")
        print("     -> Recomendado se quer encorpar a voz e zerar som nas pausas.")
        
        while True:
            choice = input("\nDigite o fluxo desejado (1 ou 2): ").strip()
            if choice in ['1', '2']:
                break
        
        print("\n[Configurações de Saída]")
        convert_mono = input("Converter para Mono? (S/N) [Recomendado]: ").upper().strip() == 'S'
        output_ext = input("Formato de saída (aac, mp3, wav): ").lower().strip()
        if output_ext not in ['aac', 'mp3', 'wav']:
            output_ext = 'aac'
            print("Formato não reconhecido, usando 'aac'.")

        flow_params = {}
        if choice == '2':
            print("\n--- Configurações do Fluxo 2 ---")
            try:
                flow_params['prop_decrease'] = float(input("Intensidade da redução base (0.0 a 1.0) [Padrão 0.8]: ") or "0.8")
            except: flow_params['prop_decrease'] = 0.8
            try:
                flow_params['highpass'] = int(input("Corte de graves em Hz [Padrão 200]: ") or "200")
            except: flow_params['highpass'] = 200
            
            dinamico = input("Focar em voz humana dinâmica (ruído de fundo)? (S/N): ").upper().strip() == 'S'
            flow_params['use_non_stationary'] = dinamico

        print(f"\nIniciando o processamento de {len(arquivos)} arquivo(s)...\n")
        
        count = 0
        for filename in arquivos:
            input_path = os.path.join(self.input_dir, filename)
            filename_base = os.path.splitext(filename)[0]
            output_path = os.path.join(self.output_dir, f"{filename_base}.{output_ext}")
            
            try:
                if choice == '1':
                    self._process_ai_flow(input_path, output_path, convert_mono, output_ext)
                else:
                    self._process_math_flow(input_path, output_path, convert_mono, output_ext, flow_params)
                count += 1
            except Exception as e:
                print(f"Erro ao processar '{filename}': {e}")
            finally:
                self._clean_temp_files()

        print(f"\nProcessamento finalizado! {count} áudios salvos em Audios_Limpos.")

    def _build_ffmpeg_final_cmd(self, input_wav, output_path, convert_mono, output_ext, extra_af=""):
        # Normalização padrão de intensidade de voz
        af = "loudnorm=I=-14:TP=-1.0:LRA=11"
        if extra_af:
            af = f"{extra_af},{af}"
            
        cmd = ["ffmpeg", "-i", input_wav, "-af", af]
        
        if convert_mono:
            cmd.extend(["-ac", "1"])
            
        if output_ext == "aac": cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        elif output_ext == "mp3": cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])
        elif output_ext == "wav": cmd.extend(["-c:a", "pcm_s16le"])
        
        cmd.extend(["-y", output_path])
        return cmd

    def _process_ai_flow(self, input_path, output_path, convert_mono, output_ext):
        print(f" [FLUXO 1 - IA] Processando: {os.path.basename(input_path)}")
        
        # Importação local para não atrasar a inicialização do app
        import torch
        from df.enhance import enhance, init_df, load_audio, save_audio
        
        # 1. FFmpeg coverte a entrada para WAV 48kHz (Formato exato exigido pela rede neural)
        subprocess.run(["ffmpeg", "-i", input_path, "-ar", "48000", "-y", self.temp1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 2. IA carrega o som no cérebro e executa a inferência
        model, df_state, _ = init_df()
        
        audio, _ = load_audio(self.temp1, sr=df_state.sr())
            
        enhanced = enhance(model, df_state, audio)
        
        # Salva o arquivo temporário isolado da voz
        save_audio(self.temp2, enhanced, df_state.sr())
        
        # 3. FFmpeg dá o polimento final (Presença + Volume)
        extra_af = "equalizer=f=3000:width_type=h:width=2000:g=3"
        cmd = self._build_ffmpeg_final_cmd(self.temp2, output_path, convert_mono, output_ext, extra_af)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("   -> Concluído.")

    def _process_math_flow(self, input_path, output_path, convert_mono, output_ext, params):
        print(f" [FLUXO 2 - ESTÚDIO] Processando: {os.path.basename(input_path)}")
        
        from scipy.io import wavfile
        import numpy as np
        import noisereduce as nr
        
        subprocess.run(["ffmpeg", "-i", input_path, "-y", self.temp1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        sr, audio_data = wavfile.read(self.temp1)
        is_stereo = len(audio_data.shape) > 1
        if is_stereo: audio_data = audio_data.T
            
        reduced = nr.reduce_noise(
            y=audio_data, 
            sr=sr, 
            prop_decrease=params['prop_decrease'], 
            stationary=not params['use_non_stationary'],
            n_std_thresh_stationary=1.5
        )
        if is_stereo: reduced = reduced.T
        wavfile.write(self.temp2, sr, reduced)
        
        # EFEITOS PODCASTER:
        # highpass: Corta o estrondo de microfone/vento
        # agate: 'Muta' o áudio quando a pessoa respira ou fica quieta
        # acompressor: Tira picos de gritos e encorpa a voz
        # equalizer: Ganho brilhante para nitidez
        hp = params.get('highpass', 200)
        podcaster_fx = (
            f"highpass=f={hp},"
            f"agate=threshold=-35dB:ratio=4:attack=10:release=100,"
            f"acompressor=threshold=-20dB:ratio=3:attack=5:release=50,"
            f"equalizer=f=3000:width_type=h:width=2000:g=5"
        )
        
        cmd = self._build_ffmpeg_final_cmd(self.temp2, output_path, convert_mono, output_ext, podcaster_fx)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("   -> Concluído.")

if __name__ == "__main__":
    app = AudioCleanerApp()
    app.run()
