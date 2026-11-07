clear all 
close all 

load("dataset.mat")


%% % Detrending: rimozione della componente costante (DC/gravità)

k = length(dataset);

for i = 1:k
    senza_gravita = zeros(size(dataset(i).matrix));
    
    for j = 1:6
        senza_gravita(:,j) = dataset(i).matrix(:,j) - mean(dataset(i).matrix(:,j));
    end

    dataset(i).senza_gravita = senza_gravita;

end

%% Verifica del rapporto segnale-rumore (SNR) per la scelta della low_cut del filtro passabanda
% questa sezione è da runnare solo una volta

Fs = 200; 

lowCut_vec = 0.001 : 0.005 : 0.5;
highCut = 25;

snr_values = zeros(size(lowCut_vec));   

for k = 1:length(lowCut_vec)
    
    lowCut = lowCut_vec(k);
    Wn = [lowCut highCut] / (Fs/2);
    [b, a] = butter(2, Wn, 'bandpass');
    
    snr_list = [];  % lista SNR di tutti i segnali
    
    % Loop sulle righe di TUTTO il dataset
    for d = 1:length(dataset)
        
        % Loop su tutte le colonne (accX, accY, accZ, gyrX, gyrY, gyrZ)
        for col = 1:size(dataset(d).senza_gravita, 2)
            
            signal = dataset(d).senza_gravita(:, col);
            filtered = filtfilt(b, a, signal);
            
            snr_list(end+1) = snr(filtered);
            
        end
    end
    
    % salvo SNR medio del dataset
    snr_values(k) = mean(snr_list);
    
end

[best_snr, best_idx] = max(snr_values);
best_low_cutoff = lowCut_vec(best_idx);

fprintf("Miglior low cutoff = %.4f Hz con SNR medio = %.2f dB\n", ...
        best_low_cutoff, best_snr);


%% Filtraggio: filtro PASSA-BANDA  (low_cut = 0.021Hz high_cut = 25Hz)

for i = 1:k
    bandpass_filter = zeros(size(dataset(i).matrix));
    
    for j = 1:6
        bandpass_filter(:,j) = filter_BandPass(dataset(i).senza_gravita(:,j));
    end

    dataset(i).bandpass_filter = bandpass_filter;    
end

%% modulo del segnale dopo il filtraggio passa-banda   

for i = 1:k
    absolute_value = zeros(size(dataset(i).matrix));
    
    for j = 1:6
        absolute_value(:,j) = abs(bandpass_filter(:,j));
    end
    
      dataset(i).absolute_value = absolute_value;     
end


%% PCA - verifica asse principale per scegliere l'asse per finestrare il segnale 

% selezione randomica dell'acquisizione 46
signal = dataset(46).bandpass_filter(:,1:6); %si può cambiare numero di acquisizione

labels = ["accx","accy","accz","gyrx","gyry","gyrz"];

[coeff, score, latent] = pca(signal);

[~, idx] = max(abs(coeff(:,1)));

dominant_signal = labels(idx)  % accx


%% verifica: PLOT FILTRO PASSA-BASSO
% da runnare nel caso di un confronto visivo fra segnale non filtrato e
% segnale filtrato 

k = 1;
Fs = 200;
signal = dataset(11).senza_gravita(:,k);
time = dataset(1).time;
 
filtered_signal = filter_BandPass(signal); 

% Plotta il segnale filtrato
figure;
plot(time, filtered_signal, 'r', 'LineWidth', 1, 'DisplayName', 'Filtrato');
hold on;
plot(time, signal, 'Color', [0.7 0.7 0.7],'DisplayName', 'Originale'); 

title('Segnale filtrato con filtro passa-basso');
xlabel('Tempo (s)');
ylabel('Ampiezza');
legend;
grid on;
hold off;

%% verifica: Algoritmo di FINESTRATURA basato sulla threshold
% da runnare solo per vedere come il segnale verrebbe tagliato

time = dataset(1).time;
accx = dataset(55).absolute_value(:,1);

% algoritmo di finestratura basato sulla threshold
ROI = detect_event_window(accx, time);

figure; 
plot(time, accx); hold on;

for i = 1:size(ROI,1)
    xline(time(ROI(i,1)), 'r', 'LineWidth', 1.5);
    xline(time(ROI(i,2)), 'g', 'LineWidth', 1.5);
end

legend('Segnale', 'Inizio finestra', 'Fine finestra');

%% CREAZIONE dataset_completo 

dataset_completo = struct([]);
count = 1;   % contatore righe del nuovo dataset

for p = 1:length(dataset)   % per ogni acquisizione

    % usa accx filtrato e assoluto per individuare le ripetizioni
    accx = dataset(p).absolute_value(:,1);
    time = dataset(p).time;

    % trova le finestre della ripetizione
    ROI = detect_event_window(accx, time);

    % per ogni ripetizione trovata
    for r = 1:size(ROI,1)

        startIdx = ROI(r,1);
        endIdx   = ROI(r,2);

        % segnali (6 colonne)
        signals_window = dataset(p).bandpass_filter(startIdx:endIdx, :);

        % tempo
        N = endIdx - startIdx + 1;     % numero campioni
        dt = 0.005;                    % passo temporale desiderato
        time_window = (0:dt:(N-1)*dt)';

        % --- crea struct riga per riga ---
        dataset_completo(count).patient_id = dataset(p).patient;
        dataset_completo(count).label      = dataset(p).label;
        dataset_completo(count).time       = time_window;
        dataset_completo(count).signals    = signals_window;

        count = count + 1;
    end
end

%% verifica finestratura
% plot di 100 segnali finestrati sovrapposti 

num_plots = 100;                     
N = length(dataset_completo);        

% Genera 100 indici casuali
idx_rand = randperm(N, num_plots);

% ------------------ FIGURA 1: ACCELERAZIONE X ------------------
figure; 
hold on;
title('200 segnali accelerazione X sovrapposti');
xlabel('Tempo [s]');
ylabel('AccX');
grid on;

for k = 1:num_plots
    idx = idx_rand(k);
    t = dataset_completo(idx).time;
    accX = dataset_completo(idx).signals(:,1);
    plot(t, accX, 'Color', [0 0 1 0.2]);   % blu trasparente
end

% ------------------ FIGURA 2: GYRO Y ------------------
figure;
hold on;
title('200 segnali giroscopio Y sovrapposti');
xlabel('Tempo [s]');
ylabel('GyrY');
grid on;

for k = 1:num_plots
    idx = idx_rand(k);
    t = dataset_completo(idx).time;
    gyrY = dataset_completo(idx).signals(:,4);
    plot(t, gyrY, 'Color', [1 0 0 0.2]);   % rosso trasparente
end

