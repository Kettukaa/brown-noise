import argparse
import numpy as np
import seaborn as sns
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.signal import lfilter, butter, sosfilt

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate and process Brownian noise.")
    parser.add_argument("--length", "-l", type=int, default=100, help="Length of the noise in seconds.")
    parser.add_argument("--sample_rate", "-sr", type=int, default=44100, help="Sample rate in Hz. [44100, 48000, 96000, etc]")
    parser.add_argument("--file_name", "-f", type=str, default="brownian_noise.wav", help="Output file name.")
    parser.add_argument("--plot", "-p", action="store_true", help="Specify this flag to save a plot.")
    parser.add_argument("--plot_file_name", "-pf", type=str, default="plot.png", help="File name for saving the plot if plot is enabled.")
    parser.add_argument("--f3dB", "-f3", type=int, default=80, help="f3dB cutoff frequency (similar to high pass filter) in Hz")
    parser.add_argument("--highpass", "-hp", dest="highpass", type=int, default=20, help="High pass filter cutoff frequency in Hz")
    parser.add_argument("--no-highpass", "-nhp", dest="do_highpass", action="store_false", help="Disable high pass filtering.")
    parser.set_defaults(highpass=True)
    return parser.parse_args()

def plot_audio_and_spectrum(audio, fs, file_name):
    """Save the waveform and frequency spectrum of the audio."""
    print("Plotting and saving audio and spectrum...")
    sns.set(style="whitegrid")
    
    n = len(audio)
    freq = np.fft.rfftfreq(n, d=1/fs)
    magnitude = np.abs(np.fft.rfft(audio)) / n
    magnitude_db = 20 * np.log10(magnitude + 1e-12)  

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plotting the waveform
    time = np.linspace(0, len(audio) / fs, num=len(audio))
    sns.lineplot(x=time, y=audio, ax=axes[0], color='b', linewidth=0.5)
    axes[0].set_title('Waveform of Brownian Noise')
    axes[0].set_xlabel('Time (seconds)')
    axes[0].set_ylabel('Amplitude')

    # Plotting the frequency spectrum
    sns.lineplot(x=freq, y=magnitude_db, ax=axes[1], color='r', linewidth=0.5)
    axes[1].set_title('Frequency Spectrum of Brownian Noise')
    axes[1].set_xlabel('Frequency (Hz)')
    axes[1].set_ylabel('Intensity (dB)')
    axes[1].set_xscale('log')
    
    plt.tight_layout()
    plt.savefig(file_name, dpi=300)
    plt.close()
    print(f"Plot saved as {file_name}")

def high_pass_filter(waveform, fs, hz=20):
    print("Applying high pass filter...")
    sos = butter(10, hz, 'hp', fs=fs, output='sos')
    filtered_signal = sosfilt(sos, waveform)
    return filtered_signal

def find_alpha(Fs, f3dB):
    """
    Calculate the alpha value for the given cutoff frequency.

    https://dsp.stackexchange.com/questions/40462/exponential-moving-average-cut-off-frequency/40465#40465
    """
    print(f"Calculating alpha for cutoff frequency {f3dB} Hz...")
    return (
            np.sqrt(
                np.power(np.cos(2 * np.pi * f3dB / Fs), 2) 
                - 4 * np.cos(2 * np.pi * f3dB / Fs) 
                + 3
            ) 
            + np.cos(2 * np.pi * f3dB / Fs) 
            - 1
    )

def generate_brownian_noise(N, alpha):
    """
    Generate brownian noise with the given alpha value.
    
    https://dsp.stackexchange.com/questions/40462/exponential-moving-average-cut-off-frequency/40465#40465
    """
    print("Generating Brownian noise...")
    x = np.random.normal(0, 1, N) 
    b = [alpha]
    a = [1, -(1-alpha)]
    y = lfilter(b, a, x)
    return y

def main():
    args = parse_arguments()
    Fs = args.sample_rate
    target_f3dB = args.f3dB
    alpha = find_alpha(Fs, target_f3dB)
    print(f"Calculated alpha: {alpha}")

    N = Fs * args.length
    brownian_noise = generate_brownian_noise(N, alpha)

    if args.do_highpass:
        brownian_noise = high_pass_filter(brownian_noise, Fs, args.highpass)
        
    max_value = np.max(abs(brownian_noise))
    brownian_noise = (brownian_noise / max_value)
    print(f"Brownian noise normalized to range [-1, 1].")

    sf.write(args.file_name, brownian_noise*0.9, Fs, subtype='PCM_24')
    print(f"Brownian noise WAV file '{args.file_name}' has been generated and saved.")

    if args.plot:
        plot_audio_and_spectrum(brownian_noise, Fs, args.plot_file_name)

if __name__ == "__main__":
    main()