clc; clear; close all;

load("dataset_completo.mat");

Fs = 200;
N_win = 256;

N = numel(dataset_completo);

% ---- costruisco una volta sola i nomi (usando il primo elemento) ----
signals0 = dataset_completo(1).signals;

feature_names = {};
fv0 = [];

for ch = 1:6
    [ft, nt] = funzione_dominio_tempo(signals0(:,ch));
    [ff, nf] = funzione_dominio_frequenza(signals0(:,ch), Fs, N_win);
    [fTF,nTF]= funzione_dominio_tempofrequenza(signals0(:,ch), Fs, N_win);

    fv0 = [fv0, ft, ff, fTF];
    feature_names = [feature_names, ...
        "ch"+ch+"_"+string(nt), ...
        "ch"+ch+"_"+string(nf), ...
        "ch"+ch+"_"+string(nTF)];
end

[fma1, nma] = funzione_multiasse(signals0(:,1:3));
[fma2, ~]   = funzione_multiasse(signals0(:,4:6));

fv0 = [fv0, fma1, fma2];
feature_names = [feature_names, ...
    "acc_"+string(nma), ...
    "gyro_"+string(nma)];

F = numel(fv0);

% ---- preallocazione ----
X = zeros(N, F);
y = strings(N,1);

% ---- loop dataset ----
for i = 1:N
    signals = dataset_completo(i).signals;

    feature_vector = [];

    for ch = 1:6
        ft  = funzione_dominio_tempo(signals(:,ch));
        ff  = funzione_dominio_frequenza(signals(:,ch), Fs, N_win);
        fTF = funzione_dominio_tempofrequenza(signals(:,ch), Fs, N_win);

        feature_vector = [feature_vector, ft, ff, fTF];
    end

    fma1 = funzione_multiasse(signals(:,1:3));
    fma2 = funzione_multiasse(signals(:,4:6));
    feature_vector = [feature_vector, fma1, fma2];

    if numel(feature_vector) ~= F
        error("Campione %d: dimensione feature diversa (atteso %d, ottenuto %d)", ...
              i, F, numel(feature_vector));
    end

    X(i,:) = feature_vector;
    y(i) = string(dataset_completo(i).label);
end
save('features_dataset.mat', 'X', 'y', 'feature_names');