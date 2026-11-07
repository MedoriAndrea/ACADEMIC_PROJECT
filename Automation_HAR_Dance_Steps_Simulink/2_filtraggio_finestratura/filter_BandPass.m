function filtered_signal = filter_BandPass(signal)
    
    % Progetta un filtro passa-banda tra 0.0210 Hz e 25 Hz
    low_cutoff = 0.0210; % Frequenza di taglio bassa
    high_cutoff = 25; % Frequenza di taglio alta
    
    Fs = 200; 
    
    % filtro del secondo ordine 
    [b, a] = butter(2, [ low_cutoff high_cutoff] / (Fs / 2), 'bandpass'); % Coefficienti del filtro
    
    % Applica il filtro al segnale
    filtered_signal = filtfilt(b, a, signal);

end