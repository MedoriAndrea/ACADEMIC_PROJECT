function [features, names] = funzione_dominio_tempofrequenza(raw_signal, Fs, N_win)

signal = double(raw_signal(:));
signal = signal - mean(signal);

win = hamming(N_win);
overlap = round(0.75*N_win);
nfft = 2*N_win;

[S, F] = stft(signal, Fs, ...
              'Window', win, ...
              'OverlapLength', overlap, ...
              'FFTLength', nfft);

S_mag = abs(S);

features = [];
names = [];

% --- STFT total energy
features = [features, sum(S_mag(:).^2)];
names    = [names, "stft_total_energy"];

% --- Dominant frequency (globale)
[~, lin_idx] = max(S_mag(:));
[f_idx, ~] = ind2sub(size(S_mag), lin_idx);

features = [features, F(f_idx)];
names    = [names, "stft_dominant_frequency"];

% --- Spectral variance over time
stft_var = var(S_mag, 0, 2);

features = [features, mean(stft_var), std(stft_var)];
names    = [names, ...
    "stft_mean_variance_over_time", ...
    "stft_std_variance_over_time"];

% --- Spectral flux
flux = sum(diff(S_mag,1,2).^2);

features = [features, mean(flux), std(flux)];
names    = [names, ...
    "stft_spectral_flux_mean", ...
    "stft_spectral_flux_std"];
end
