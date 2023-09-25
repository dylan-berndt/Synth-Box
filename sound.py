
import numpy as np


pitch_window = 1000


def pitch_shift(audio, semitones):
    data = np.zeros(len(audio))
    for i in range(0, len(audio), pitch_window):
        sample = audio[i:i + pitch_window]
        data[i:i + pitch_window] += pitch_shift_section(sample, semitones)
    return data


def pitch_shift_section(audio, semitones):
    factor = 2.0 ** (float(semitones) / 12)

    x = np.fft.fft(audio)
    N = int(len(x) / 2) + 1 if len(x) % 2 == 0 else int((len(x) + 1) / 2)
    y = np.zeros(N, dtype=np.complex)

    for i in range(N):
        ix = int(i * factor)
        if ix < N:
            y[ix] += x[i]

    Y = np.r_[y, np.conj(y[-2:0:-1])] if len(x) % 2 == 0 else np.r_[y, np.conj(y[-1:0:-1])]

    return np.real(np.fft.ifft(Y))
