clc; clear;

% 1) Carica le feature già estratte
load('features_dataset.mat');  
% deve contenere: X (1000x162), y, feature_names

TARGET_VAR = 95;

% 2) Media e deviazione standard (sulle feature ORIGINALI)
mu    = mean(X, 1);
sigma = std(X, 0, 1) + eps;

% 3) Standardizzazione
X_std = (X - mu) ./ sigma;

% 4) PCA
[coeff, score, latent, tsquared, explained] = pca(X_std);

% 5) Numero di componenti per la varianza target
cumExpl = cumsum(explained);
k_optimum = find(cumExpl >= TARGET_VAR, 1, 'first');

% 6) Matrice PCA (loadings)
coeffK = coeff(:, 1:k_optimum);

% 7) Salvataggio parametri PCA (SERVONO ONLINE)
save('pca_params.mat', 'mu', 'sigma', 'coeffK', 'k_optimum');

fprintf('PCA pronta: %d componenti per %.1f%% di varianza\n', ...
        k_optimum, cumExpl(k_optimum));
