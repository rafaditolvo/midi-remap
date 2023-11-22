import mido
import tkinter as tk
from tkinter import filedialog

class MidiNoteEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("MIDI Note Editor")

        self.file_path = None
        self.note_mapping = {}
        self.available_notes = []

        # Botão para carregar arquivo MIDI
        self.load_button = tk.Button(self.master, text="Carregar MIDI", command=self.load_midi)
        self.load_button.pack(pady=10)

        # Rótulo para exibir informações
        self.info_label = tk.Label(self.master, text="")
        self.info_label.pack(pady=10)

        # Campo de entrada para transposição
        self.from_note_label = tk.Label(self.master, text="Transpor de:")
        self.from_note_label.pack(pady=5)

        self.from_note_var = tk.StringVar(self.master)
        self.from_note_dropdown = tk.OptionMenu(self.master, self.from_note_var, "")
        self.from_note_dropdown.pack(pady=5)

        self.to_note_label = tk.Label(self.master, text="Para:")
        self.to_note_label.pack(pady=5)

        self.to_note_var = tk.StringVar(self.master)
        self.to_note_dropdown = tk.OptionMenu(self.master, self.to_note_var, "")
        self.to_note_dropdown.pack(pady=5)

        # Botão para aplicar a transposição
        self.transpose_button = tk.Button(self.master, text="Aplicar Transposição", state=tk.DISABLED, command=self.transpose_notes)
        self.transpose_button.pack(pady=10)

        # Botão para salvar o arquivo MIDI modificado
        self.save_button = tk.Button(self.master, text="Salvar MIDI", state=tk.DISABLED, command=self.save_midi)
        self.save_button.pack(pady=10)

    def load_midi(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Arquivos MIDI", "*.mid")])

        if self.file_path:
            self.note_mapping, ticks_per_beat = self.read_midi_info(self.file_path)
            self.available_notes = sorted(self.note_mapping.keys())
            self.populate_note_dropdowns()

            self.info_label.config(text=f"Arquivo MIDI carregado: {self.file_path}\nTicks por batida: {ticks_per_beat}")
            self.transpose_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)

    def populate_note_dropdowns(self):
        menu = self.from_note_dropdown["menu"]
        menu.delete(0, "end")
        for note in self.available_notes:
            menu.add_command(label=note, command=lambda value=note: self.from_note_var.set(value))

        menu = self.to_note_dropdown["menu"]
        menu.delete(0, "end")
        for note in self.available_notes + self.get_full_note_range():
            menu.add_command(label=note, command=lambda value=note: self.to_note_var.set(value))

    def read_midi_info(self, input_file):
        mid = mido.MidiFile(input_file)
        note_mapping = {}

        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' or msg.type == 'note_off':
                    note = msg.note
                    velocity = msg.velocity
                    time = msg.time

                    note_name = self.note_number_to_name(note)

                    if note_name not in note_mapping:
                        note_mapping[note_name] = {'velocity': velocity, 'times': [time]}
                    else:
                        note_mapping[note_name]['times'].append(time)

        return note_mapping, mid.ticks_per_beat

    def note_name_to_number(self, note_name):
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note = note_name[:-1]
        octave = int(note_name[-1])
        note_number = note_names.index(note) + 12 * (octave + 2)  # Ajuste aqui
        return note_number

    def note_number_to_name(self, note_number):
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note_name = note_names[(note_number - 12) % 12]
        octave = (note_number - 12) // 12 - 1  # Ajuste aqui
        return f'{note_name}{octave}'

    def get_full_note_range(self):
        note_range = [f'{note_name}{octave}' for octave in range(8) for note_name in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']]
        return note_range

    def transpose_notes(self):
        from_note = self.from_note_var.get()
        to_note = self.to_note_var.get()

        if not from_note or not to_note:
            self.info_label.config(text="Erro: Selecione notas de e para.")
            return

        try:
            transpose_value = self.note_name_to_number(to_note) - self.note_name_to_number(from_note)

            # Crie uma cópia do mapeamento de notas antes da transposição
            original_note_mapping = self.note_mapping.copy()

            # Limpe o mapeamento de notas atual
            self.note_mapping = {}

            # Transponha as notas
            for original_note_name, data in original_note_mapping.items():
                transposed_note_name = self.transpose_note_name(original_note_name, transpose_value)
                self.note_mapping[transposed_note_name] = {'velocity': data['velocity'], 'times': data['times']}

            self.info_label.config(text="Transposição aplicada com sucesso.")
        except ValueError:
            self.info_label.config(text="Erro: Falha na transposição. Verifique as notas selecionadas.")

    def transpose_note_name(self, note_name, transpose_value):
        original_note_number = self.note_name_to_number(note_name)
        transposed_note_number = original_note_number + transpose_value
        transposed_note_name = self.note_number_to_name(transposed_note_number)
        return transposed_note_name

    def save_midi(self):
        output_file = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("Arquivos MIDI", "*.mid")])

        if output_file:
            midi = mido.MidiFile()
            track = mido.MidiTrack()
            midi.tracks.append(track)

            for note_name, data in self.note_mapping.items():
                note_number = self.note_name_to_number(note_name)
                velocity = data['velocity']

                for time in data['times']:
                    if time < 0:
                        time = 0

                    track.append(mido.Message('note_on', note=note_number, velocity=velocity, time=time))
                    track.append(mido.Message('note_off', note=note_number, velocity=0, time=0))

            midi.save(output_file)
            self.info_label.config(text=f"Arquivo MIDI salvo em: {output_file}")

# Inicie o aplicativo
if __name__ == "__main__":
    root = tk.Tk()
    app = MidiNoteEditor(root)
    root.mainloop()
